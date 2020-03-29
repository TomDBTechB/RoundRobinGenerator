import csv
import os

from gurobipy import GurobiError, Model, GRB, quicksum
import numpy as np


# run everything to 4d cycle
# learn the model

def generate_multi_dim_sample(bounds, directory, num_teams, num_md_per_cycle, numSam, numCycle):
    # the list of sample dimensions, the +1
    cycle = list(range(numCycle))
    day = list(range(num_md_per_cycle))
    home = away = list(range(num_teams))

    constrList = [[(0,), (1,)], [(0,), (2,)], [(0,), (3,)], [(0,), (1, 2)], [(0,), (1, 3)], [(0,), (2, 3)],
                  [(0,), (1, 2, 3)],
                  [(1,), (0,)], [(1,), (2,)], [(1,), (3,)], [(1,), (0, 2)], [(1,), (0, 3)], [(1,), (2, 3)],
                  [(1,), (0, 2, 3)],
                  [(2,), (0,)], [(2,), (1,)], [(2,), (3,)], [(2,), (0, 1)], [(2,), (0, 3)], [(2,), (1, 3)],
                  [(2,), (0, 1, 3)],
                  [(3,), (0,)], [(3,), (1,)], [(3,), (2,)], [(3,), (0, 1)], [(3,), (0, 2)], [(3,), (1, 2)],
                  [(3,), (0, 1, 2)],
                  [(0, 1), (2,)], [(0, 1), (3,)], [(0, 1), (2, 3)],
                  # cons away = 31
                  [(0, 2), (1,)], [(0, 2), (3,)], [(0, 2), (1, 3)],
                  # cons home = 34
                  [(0, 3), (1,)], [(0, 3), (2,)], [(0, 3), (1, 2)],
                  [(1, 2), (0,)], [(1, 2), (3,)], [(1, 2), (0, 3)],
                  [(1, 3), (0,)], [(1, 3), (2,)], [(1, 3), (0, 2)],
                  [(2, 3), (0,)], [(2, 3), (1,)], [(2, 3), (0, 1)],
                  [(0, 1, 2), (3,)],
                  [(0, 1, 3), (2,)],
                  [(0, 2, 3), (1,)],
                  [(1, 2, 3), (0,)]]

    try:
        model = Model("sspSolver")
        # give verbose logging when 1, otherwise 0
        model.setParam(GRB.param.OutputFlag, 0)

        ### Decision Variables ###
        # 0 = cycles, 1 = days, 2 = away, 3 = home
        # regular combinations over the 4 dimensions
        x = model.addVars(cycle, day, home, away, vtype=GRB.BINARY, name="base")
        n = model.addVars(cycle, day, home, vtype=GRB.BINARY, name="n")
        o = model.addVars(cycle, day, away, vtype=GRB.BINARY, name="o")
        p = model.addVars(cycle, home, away, vtype=GRB.BINARY, name="p")
        q = model.addVars(day, home, away, vtype=GRB.BINARY, name="q")
        r = model.addVars(cycle, day, vtype=GRB.BINARY, name="r")
        s = model.addVars(cycle, home, vtype=GRB.BINARY, name="s")
        t = model.addVars(cycle, away, vtype=GRB.BINARY, name="t")
        u = model.addVars(day, home, vtype=GRB.BINARY, name="u")
        v = model.addVars(day, away, vtype=GRB.BINARY, name="v")
        w = model.addVars(home, away, vtype=GRB.BINARY, name="w")


        consHome = model.addVars(cycle, day, day, home)
        consAway = model.addVars(cycle, day, day, away)
        consNotAway = model.addVars(cycle, day, day, away)
        consNotHome = model.addVars(cycle, day, day, home)


        ### Hard constraints -- not yet in bounds ###
        # never play yourself
        model.addConstrs(x[c,d,i,i]==0 for c in cycle for d in day for i in home)
        # only play one game per day
        model.addConstrs((x.sum(c,d,i,'*') + x.sum(c,d,'*', i) <= 1 for c in cycle for d in day for i in home), "1gamePerDay")


        ### Hard constraints from bounds files ###
        # bounds 0 = countLowerbound
        # bounds 1 = countUpperBound
        # bounds 2 = minConsZero
        # bounds 3 = maxConsZero
        # bounds 4 = minConsNonZero
        # bounds 5 = maxConsNonZero
        for i in range(len(bounds)):
            ### SEED COUNT BOUNDS: bounds[i,0] is the lowerbound, bounds[i,1] is the upperbound
            if bounds[i, 0] > 0:
                # this part covers count lowerbound
                if constrList[i] == [(0,), (1,)]:
                    model.addConstrs((r.sum(c, '*') >= bounds[i, 0] for c in cycle), "LWR_constr-(0,), (1,)")
                elif constrList[i] == [(0,), (2,)]:
                    model.addConstrs((t.sum(c, '*') >= bounds[i, 0] for c in cycle), "LWR_constr-(0,), (2,)")
                elif constrList[i] == [(0,), (3,)]:
                    model.addConstrs((s.sum(c, '*') >= bounds[i, 0] for c in cycle), "LWR_constr-(0,), (3,)")
                elif constrList[i] == [(0,), (1, 2)]:
                    model.addConstrs((o.sum(c, '*', '*') >= bounds[i, 0] for c in cycle), "LWR_constr-(0,), (1,2)")
                elif constrList[i] == [(0,), (1, 3)]:
                    model.addConstrs((n.sum(c, '*', '*') >= bounds[i, 0] for c in cycle), "LWR_constr-(0,), (1,3)")
                elif constrList[i] == [(0,), (2, 3)]:
                    model.addConstrs((p.sum(c, '*', '*') >= bounds[i, 0] for c in cycle), "LWR_constr-(0,), (2,3)")
                elif constrList[i] == [(0,), (1, 2, 3)]:
                    model.addConstrs((x.sum(c, '*', '*', '*') >= bounds[i, 0] for c in cycle),
                                     "LWR_constr-(0,), (1,2,3)")

                elif constrList[i] == [(1,), (0,)]:
                    model.addConstrs((r.sum('*', d) >= bounds[i, 0] for d in day), "LWR_constr-(1,), (0,)")
                elif constrList[i] == [(1,), (2,)]:
                    model.addConstrs((u.sum(d, '*') >= bounds[i, 0] for d in day), "LWR_constr-(1,), (2,)")
                elif constrList[i] == [(1,), (3,)]:
                    model.addConstrs((v.sum(d, '*') >= bounds[i, 0] for d in day), "LWR_constr-(1,), (3,)")
                elif constrList[i] == [(1,), (0, 2)]:
                    model.addConstrs((o.sum('*', d, '*') >= bounds[i, 0] for d in day), "LWR_constr-(1,), (0,2)")
                elif constrList[i] == [(1,), (0, 3)]:
                    model.addConstrs((n.sum('*', d, '*') >= bounds[i, 0] for d in day), "LWR_constr-(1,), (0,3)")
                elif constrList[i] == [(1,), (2, 3)]:
                    model.addConstrs((q.sum(d, '*', '*') >= bounds[i, 0] for d in day), "LWR_constr-(1,), (2,3)")
                elif constrList[i] == [(1,), (0, 2, 3)]:
                    model.addConstrs((x.sum('*', d, '*', '*') >= bounds[i, 0] for d in day), "LWR_constr-(1,), (0,2,3)")

                elif constrList[i] == [(2,), (0,)]:
                    model.addConstrs((t.sum('*', h) >= bounds[i, 0] for h in home), "LWR_constr-(2,), (0,)")
                elif constrList[i] == [(2,), (1,)]:
                    model.addConstrs((u.sum('*', h) >= bounds[i, 0] for h in home), "LWR_constr-(2,), (1,)")
                elif constrList[i] == [(2,), (3,)]:
                    model.addConstrs((w.sum(h, '*') >= bounds[i, 0] for h in home), "LWR_constr--(2,), (3,)")
                elif constrList[i] == [(2,), (0, 1)]:
                    model.addConstrs((o.sum('*', '*', h) >= bounds[i, 0] for h in home), "LWR_constr--(2,), (0,1)")
                elif constrList[i] == [(2,), (0, 3)]:
                    model.addConstrs((p.sum('*', h, '*') >= bounds[i, 0] for h in home), "LWR_constr--(2,), (0,3)")
                elif constrList[i] == [(2,), (1, 3)]:
                    model.addConstrs((q.sum('*', h, '*') >= bounds[i, 0] for h in home), "LWR_constr-(2,), (1,3)")
                elif constrList[i] == [(2,), (0, 1, 3)]:
                    model.addConstrs((x.sum('*', '*', h, '*') >= bounds[i, 0] for h in home),
                                     "LWR_constr-(2,), (0,1,3)")

                elif constrList[i] == [(3,), (0,)]:
                    model.addConstrs((s.sum('*', a) >= bounds[i, 0] for a in away), "LWR_constr-(3,), (0,)")
                elif constrList[i] == [(3,), (1,)]:
                    model.addConstrs((v.sum('*', a) >= bounds[i, 0] for a in away), "LWR_constr-(3,), (1,)")
                elif constrList[i] == [(3,), (2,)]:
                    model.addConstrs((w.sum('*', a) >= bounds[i, 0] for a in away), "LWR_constr-(3,), (2,)")
                elif constrList[i] == [(3,), (0, 1)]:
                    model.addConstrs((n.sum('*', '*', a) >= bounds[i, 0] for a in away), "LWR_constr-(3,), (0,1)")
                elif constrList[i] == [(3,), (0, 2)]:
                    model.addConstrs((p.sum('*', '*', a) >= bounds[i, 0] for a in away), "LWR_constr-(3,), (0,2)")
                elif constrList[i] == [(3,), (1, 2)]:
                    model.addConstrs((q.sum('*', '*', a) >= bounds[i, 0] for a in away), "LWR_constr-(3,), (1,2)")
                elif constrList[i] == [(3,), (0, 1, 2)]:
                    model.addConstrs((x.sum('*', '*', '*', a) >= bounds[i, 0] for a in away),
                                     "LWR_constr-(3,), (0,1,2)")

                elif constrList[i] == [(0, 1), (2,)]:
                    model.addConstrs((o.sum(c, d, '*') >= bounds[i, 0] for c in cycle for d in day),
                                     "LWR_constr-(0,1), (2,)")
                elif constrList[i] == [(0, 1), (3,)]:
                    model.addConstrs((n.sum(c, d, '*') >= bounds[i, 0] for c in cycle for d in day),
                                     "LWR_constr-(0,1), (3,)")
                elif constrList[i] == [(0, 1), (2, 3)]:
                    model.addConstrs((x.sum(c, d, '*', '*') >= bounds[i, 0] for c in cycle for d in day),
                                     "LWR_constr-(0,1), (2,3)")

                elif constrList[i] == [(0, 2), (1,)]:
                    model.addConstrs((n.sum(c, '*', a) >= bounds[i, 0] for c in cycle for a in away),
                                     "LWR_constr-(0,2), (1,)")
                elif constrList[i] == [(0, 2), (3,)]:
                    model.addConstrs((p.sum(c, '*', a) >= bounds[i, 0] for c in cycle for a in away),
                                     "LWR_constr-(0,2), (3,)")
                elif constrList[i] == [(0, 2), (1, 3)]:
                    model.addConstrs((x.sum(c, '*', a) >= bounds[i, 0] for c in cycle for a in away),
                                     "LWR_constr-(0,2), (1,3)")

                elif constrList[i] == [(0, 3), (1,)]:
                    model.addConstrs((n.sum(c, '*', h) >= bounds[i, 0] for c in cycle for h in home),
                                     "LWR_constr-(0,3), (1,)")
                elif constrList[i] == [(0, 3), (2,)]:
                    model.addConstrs((p.sum(c, '*', h) >= bounds[i, 0] for c in cycle for h in home),
                                     "LWR_constr-(0,3), (2,)")
                elif constrList[i] == [(0, 3), (1, 2)]:
                    model.addConstrs((x.sum(c, '*', '*', h) >= bounds[i, 0] for c in cycle for h in home),
                                     "LWR_constr-(0,3), (1,2)")

                elif constrList[i] == [(1, 2), (0,)]:
                    model.addConstrs((o.sum('*', d, a) >= bounds[i, 0] for d in day for a in away),
                                     "LWR_constr-(1,2), (0,)")
                elif constrList[i] == [(1, 2), (3,)]:
                    model.addConstrs((q.sum(d, a, '*') >= bounds[i, 0] for d in day for a in away),
                                     "LWR_constr-(1,2), (3,)")
                elif constrList[i] == [(1, 2), (0, 3)]:
                    model.addConstrs((x.sum('*', d, a, '*') >= bounds[i, 0] for d in day for a in away),
                                     "LWR_constr-(1,2), (0,3)")

                elif constrList[i] == [(1, 3), (0,)]:
                    model.addConstrs((n.sum('*', d, h) >= bounds[i, 0] for d in day for h in home),
                                     "LWR_constr-(1,3), (0,)")
                elif constrList[i] == [(1, 3), (2,)]:
                    model.addConstrs((q.sum(d, '*', h) >= bounds[i, 0] for d in day for h in home),
                                     "LWR_constr-(1,3), (2,)")
                elif constrList[i] == [(1, 3), (0, 2)]:
                    model.addConstrs((x.sum('*', d, '*', h) >= bounds[i, 0] for d in day for h in home),
                                     "LWR_constr-(1,3), (0,2)")

                elif constrList[i] == [(2, 3), (0,)]:
                    model.addConstrs((p.sum('*', h, a) >= bounds[i, 0] for h in home for a in away),
                                     "LWR_constr-(2,3), (0,)")
                elif constrList[i] == [(2, 3), (1,)]:
                    model.addConstrs((q.sum('*', h, a) >= bounds[i, 0] for h in home for a in away),
                                     "LWR_constr-(2,3), (1,)")
                elif constrList[i] == [(2, 3), (0, 1)]:
                    model.addConstrs((x.sum('*', '*', h, a) >= bounds[i, 0] for h in home for a in away),
                                     "LWR_constr-(2,3), (0,1)")

                elif constrList[i] == [(0, 1, 2), (3,)]:
                    model.addConstrs((x.sum(c, d, a, '*') >= bounds[i, 0] for c in cycle for d in day for a in away),
                                     "LWR_constr-(0,1,2), (3,)")
                elif constrList[i] == [(0, 1, 3), (2,)]:
                    model.addConstrs((x.sum(c, d, '*', h) >= bounds[i, 0] for c in cycle for d in day for h in home),
                                     "LWR_constr-(0,1,3), (2,)")
                elif constrList[i] == [(0, 2, 3), (1,)]:
                    model.addConstrs((x.sum(c, '*', a, h) >= bounds[i, 0] for c in cycle for a in away for h in home),
                                     "LWR_constr-(0,2,3), (1,)")
                elif constrList[i] == [(1, 2, 3), (0,)]:
                    model.addConstrs((x.sum('*', d, a, h) >= bounds[i, 0] for d in day for a in away for h in home),
                                     "LWR_constr-(1,2,3), (0,)")
            if bounds[i, 1] > 0:
                # this part covers count lowerbound
                if constrList[i] == [(0,), (1,)]:
                    model.addConstrs((r.sum(c, '*') <= bounds[i, 1] for c in cycle), "constr-(0,), (1,)")
                elif constrList[i] == [(0,), (2,)]:
                    model.addConstrs((t.sum(c, '*') <= bounds[i, 1] for c in cycle), "constr-(0,), (2,)")
                elif constrList[i] == [(0,), (3,)]:
                    model.addConstrs((s.sum(c, '*') <= bounds[i, 1] for c in cycle), "constr-(0,), (3,)")
                elif constrList[i] == [(0,), (1, 2)]:
                    model.addConstrs((o.sum(c, '*', '*') <= bounds[i, 1] for c in cycle), "constr-(0,), (1,2)")
                elif constrList[i] == [(0,), (1, 3)]:
                    model.addConstrs((n.sum(c, '*', '*') <= bounds[i, 1] for c in cycle), "constr-(0,), (1,3)")
                elif constrList[i] == [(0,), (2, 3)]:
                    model.addConstrs((p.sum(c, '*', '*') <= bounds[i, 1] for c in cycle), "constr-(0,), (2,3)")
                elif constrList[i] == [(0,), (1, 2, 3)]:
                    model.addConstrs((x.sum(c, '*', '*', '*') <= bounds[i, 1] for c in cycle),
                                     "constr-(0,), (1,2,3)")

                elif constrList[i] == [(1,), (0,)]:
                    model.addConstrs((r.sum('*', d) <= bounds[i, 1] for d in day), "LWR_constr-(1,), (0,)")
                elif constrList[i] == [(1,), (2,)]:
                    model.addConstrs((u.sum(d, '*') <= bounds[i, 1] for d in day), "LWR_constr-(1,), (2,)")
                elif constrList[i] == [(1,), (3,)]:
                    model.addConstrs((v.sum(d, '*') <= bounds[i, 1] for d in day), "LWR_constr-(1,), (3,)")
                elif constrList[i] == [(1,), (0, 2)]:
                    model.addConstrs((o.sum('*', d, '*') <= bounds[i, 1] for d in day), "LWR_constr-(1,), (0,2)")
                elif constrList[i] == [(1,), (0, 3)]:
                    model.addConstrs((n.sum('*', d, '*') <= bounds[i, 1] for d in day), "LWR_constr-(1,), (0,3)")
                elif constrList[i] == [(1,), (2, 3)]:
                    model.addConstrs((q.sum(d, '*', '*') <= bounds[i, 1] for d in day), "LWR_constr-(1,), (2,3)")
                elif constrList[i] == [(1,), (0, 2, 3)]:
                    model.addConstrs((x.sum('*', d, '*', '*') <= bounds[i, 1] for d in day), "LWR_constr-(1,), (0,2,3)")

                elif constrList[i] == [(2,), (0,)]:
                    model.addConstrs((t.sum('*', h) <= bounds[i, 1] for h in home), "constr-(2,), (0,)")
                elif constrList[i] == [(2,), (1,)]:
                    model.addConstrs((u.sum('*', h) <= bounds[i, 1] for h in home), "constr-(2,), (1,)")
                elif constrList[i] == [(2,), (3,)]:
                    model.addConstrs((w.sum(h, '*') <= bounds[i, 1] for h in home), "constr--(2,), (3,)")
                elif constrList[i] == [(2,), (0, 1)]:
                    model.addConstrs((o.sum('*', '*', h) <= bounds[i, 1] for h in home), "constr--(2,), (0,1)")
                elif constrList[i] == [(2,), (0, 3)]:
                    model.addConstrs((p.sum('*', h, '*') <= bounds[i, 1] for h in home), "constr--(2,), (0,3)")
                elif constrList[i] == [(2,), (1, 3)]:
                    model.addConstrs((q.sum('*', h, '*') <= bounds[i, 1] for h in home), "constr-(2,), (1,3)")
                elif constrList[i] == [(2,), (0, 1, 3)]:
                    model.addConstrs((x.sum('*', '*', h, '*') <= bounds[i, 1] for h in home),
                                     "LWR_constr-(2,), (0,1,3)")

                elif constrList[i] == [(3,), (0,)]:
                    model.addConstrs((s.sum('*', a) <= bounds[i, 1] for a in away), "constr-(3,), (0,)")
                elif constrList[i] == [(3,), (1,)]:
                    model.addConstrs((v.sum('*', a) <= bounds[i, 1] for a in away), "constr-(3,), (1,)")
                elif constrList[i] == [(3,), (2,)]:
                    model.addConstrs((w.sum('*', a) <= bounds[i, 1] for a in away), "constr-(3,), (2,)")
                elif constrList[i] == [(3,), (0, 1)]:
                    model.addConstrs((n.sum('*', '*', a) <= bounds[i, 1] for a in away), "constr-(3,), (0,1)")
                elif constrList[i] == [(3,), (0, 2)]:
                    model.addConstrs((p.sum('*', '*', a) <= bounds[i, 1] for a in away), "constr-(3,), (0,2)")
                elif constrList[i] == [(3,), (1, 2)]:
                    model.addConstrs((q.sum('*', '*', a) <= bounds[i, 1] for a in away), "constr-(3,), (1,2)")
                elif constrList[i] == [(3,), (0, 1, 2)]:
                    model.addConstrs((x.sum('*', '*', '*', a) <= bounds[i, 1] for a in away),
                                     "constr-(3,), (0,1,2)")

                elif constrList[i] == [(0, 1), (2,)]:
                    model.addConstrs((o.sum(c, d, '*') <= bounds[i, 1] for c in cycle for d in day),
                                     "constr-(0,1), (2,)")
                elif constrList[i] == [(0, 1), (3,)]:
                    model.addConstrs((n.sum(c, d, '*') <= bounds[i, 1] for c in cycle for d in day),
                                     "constr-(0,1), (3,)")
                elif constrList[i] == [(0, 1), (2, 3)]:
                    model.addConstrs((x.sum(c, d, '*', '*') <= bounds[i, 1] for c in cycle for d in day),
                                     "constr-(0,1), (2,3)")

                elif constrList[i] == [(0, 2), (1,)]:
                    model.addConstrs((n.sum(c, '*', a) <= bounds[i, 1] for c in cycle for a in away),
                                     "constr-(0,2), (1,)")
                elif constrList[i] == [(0, 2), (3,)]:
                    model.addConstrs((p.sum(c, '*', a) <= bounds[i, 1] for c in cycle for a in away),
                                     "constr-(0,2), (3,)")
                elif constrList[i] == [(0, 2), (1, 3)]:
                    model.addConstrs((x.sum(c, '*', a) <= bounds[i, 1] for c in cycle for a in away),
                                     "constr-(0,2), (1,3)")

                elif constrList[i] == [(0, 3), (1,)]:
                    model.addConstrs((n.sum(c, '*', h) <= bounds[i, 1] for c in cycle for h in home),
                                     "constr-(0,3), (1,)")
                elif constrList[i] == [(0, 3), (2,)]:
                    model.addConstrs((p.sum(c, '*', h) <= bounds[i, 1] for c in cycle for h in home),
                                     "constr-(0,3), (2,)")
                elif constrList[i] == [(0, 3), (1, 2)]:
                    model.addConstrs((x.sum(c, '*', '*', h) <= bounds[i, 1] for c in cycle for h in home),
                                     "constr-(0,3), (1,2)")

                elif constrList[i] == [(1, 2), (0,)]:
                    model.addConstrs((o.sum('*', d, a) <= bounds[i, 1] for d in day for a in away),
                                     "constr-(1,2), (0,)")
                elif constrList[i] == [(1, 2), (3,)]:
                    model.addConstrs((q.sum(d, a, '*') <= bounds[i, 1] for d in day for a in away),
                                     "constr-(1,2), (3,)")
                elif constrList[i] == [(1, 2), (0, 3)]:
                    model.addConstrs((x.sum('*', d, a, '*') <= bounds[i, 1] for d in day for a in away),
                                     "constr-(1,2), (0,3)")

                elif constrList[i] == [(1, 3), (0,)]:
                    model.addConstrs((n.sum('*', d, h) <= bounds[i, 1] for d in day for h in home),
                                     "constr-(1,3), (0,)")
                elif constrList[i] == [(1, 3), (2,)]:
                    model.addConstrs((q.sum(d, '*', h) <= bounds[i, 1] for d in day for h in home),
                                     "constr-(1,3), (2,)")
                elif constrList[i] == [(1, 3), (0, 2)]:
                    model.addConstrs((x.sum('*', d, '*', h) <= bounds[i, 1] for d in day for h in home),
                                     "constr-(1,3), (0,2)")

                elif constrList[i] == [(2, 3), (0,)]:
                    model.addConstrs((p.sum('*', h, a) <= bounds[i, 1] for h in home for a in away),
                                     "constr-(2,3), (0,)")
                elif constrList[i] == [(2, 3), (1,)]:
                    model.addConstrs((q.sum('*', h, a) <= bounds[i, 1] for h in home for a in away),
                                     "constr-(2,3), (1,)")
                elif constrList[i] == [(2, 3), (0, 1)]:
                    model.addConstrs((x.sum('*', '*', h, a) <= bounds[i, 1] for h in home for a in away),
                                     "constr-(2,3), (0,1)")

                elif constrList[i] == [(0, 1, 2), (3,)]:
                    model.addConstrs((x.sum(c, d, a, '*') <= bounds[i, 1] for c in cycle for d in day for a in away),
                                     "constr-(0,1,2), (3,)")
                elif constrList[i] == [(0, 1, 3), (2,)]:
                    model.addConstrs((x.sum(c, d, '*', h) <= bounds[i, 1] for c in cycle for d in day for h in home),
                                     "constr-(0,1,3), (2,)")


                elif constrList[i] == [(0, 2, 3), (1,)]:
                    model.addConstrs((x.sum(c, '*', a, h) <= bounds[i, 1] for c in cycle for a in away for h in home),
                                     "constr-(0,2,3), (1,)")
                elif constrList[i] == [(1, 2, 3), (0,)]:
                    model.addConstrs((x.sum('*', d, a, h) <= bounds[i, 1] for d in day for a in away for h in home),
                                     "constr-(1,2,3), (0,)")

        # maximum cons of awaygames (definition)
        if bounds[31, 5] + bounds[31, 4] > 0:
            model.addConstrs((consAway[c, 0, 0, a] == o[c, 0, a] for a in away for c in cycle), "maxConsAway")
            model.addConstrs((consAway[c, d1 + 1, 0, a] <= o[c, d1 + 1, a] for a in away for c in cycle for d1 in day if
                              d1 < len(day) - 1), "MaxConsAway")
            model.addConstrs((consAway[c, d1 + 1, 0, a] <= 1 - o[c, d1, a] for a in away for c in cycle for d1 in day if
                              d1 < len(day) - 1), "MaxConsAway")

            model.addConstrs((consAway[c, 0, d2, a] == 0 for c in cycle for d2 in day for a in away if d2 > 0),
                             "MaxConsAway")
            model.addConstrs(
                (consHome[c, d1, d2, a] <= consHome[c, d1 - 1, d2 - 1, a] for c in cycle for d1 in day for d2 in day for
                 a in away if d1 > 0 if d2 > 0), "MaxConsAway")
            model.addConstrs(
                (consHome[c, d1, d2, a] <= o[c, d1, a] for c in cycle for d1 in day for d2 in day for a in away),
                "MaxConsAway")
            model.addConstrs(
                (consHome[c, d1, d2, a] >= o[c, d1, a] + consHome[c, d1 - 1, d2 - 1, a] - 1 for c in cycle for d1 in day
                 for d2 in day for a in away if d1 > 0 if d2 > 0), "MaxConsAway")
            # maximum number of away games applying
            if bounds[31, 5] > 0:
                model.addConstr(
                    (quicksum(
                        consHome[c, d1, d2, a] for c in cycle for d1 in day for d2 in range((bounds[31, 5].astype(int)), len(day)) for
                        a in away) == 0), "maxConsAway")

            # skip over minimum consecutive of away games since this is 1 and already deferred from other count constraints

        # maximum number of home trips (consecutive games not playing away)

        if bounds[31, 3] + bounds[31, 2] > 0:
            model.addConstrs((consNotAway[c, 0, 0, a] == 1 - o[c, 0, a] for c in cycle for a in away),
                             "MaxConsHomeStead")
            model.addConstrs(
                (consNotAway[c, d1 + 1, 0, a] <= o[c, d1, a] for c in cycle for a in away for d1 in day if
                 d1 < len(day) - 1),
                "MaxConsHomeStead")
            model.addConstrs(
                (consNotAway[c, d1 + 1, 0, a] <= 1 - o[c, d1 + 1, a] for c in cycle for d1 in day for a in away if
                 d1 < len(day) - 1), "MaxConsHomeStead")
            model.addConstrs(
                (consNotAway[c, d1 + 1, 0, a] >= o[c, d1, a] - o[c, d1 + 1, a] for c in cycle for d1 in day for a in
                 away if d1 < len(day) - 1), "MaxConsHomeStead")

            model.addConstrs((consNotAway[c, 0, d2, a] == 0 for c in cycle for d2 in day for a in away if d2 > 0))
            model.addConstrs((consNotAway[c, d1, d2, a] <= consNotAway[c, d1 - 1, d2 - 1, a]
                              for c in cycle for d1 in day for d2 in day for a in away if d1 > 0 if d2 > 0),
                             "MaxConsHomeStead")
            model.addConstrs((consNotAway[c, d1, d2, a] <= 1 - o[c, d1, a]
                              for c in cycle for d1 in day for d2 in day for a in away if d1 > 0 if d2 > 0),
                             "MaxConsHomeStead")
            model.addConstrs((consNotAway[c, d1, d2, a] >= consNotAway[c, d1 - 1, d2 - 1, a] - p[c, d1, a]
                              for c in cycle for d1 in day for d2 in day for a in away if d1 > 0 if d2 > 0),
                             "MaxConsHomeStead")
            if bounds[31, 3] > 0:
                model.addConstr(
                    (quicksum(
                        consNotAway[c, d1, d2, a] for c in cycle for d1 in day for d2 in range(bounds[31, 3].astype(int), len(day))
                        for a in away) == 0),
                    "maxconsfree"
                )

        # maximum cons of homegames (definition)
        if bounds[34, 5] + bounds[34, 4] > 0:
            model.addConstrs((consHome[c, 0, 0, h] == n[c, 0, h] for h in home for c in cycle), "maxConsHome")
            model.addConstrs((consHome[c, d1 + 1, 0, h] <= n[c, d1 + 1, h] for h in home for c in cycle for d1 in day if
                              d1 < len(day) - 1), "MaxConsHome")
            model.addConstrs((consHome[c, d1 + 1, 0, h] <= 1 - n[c, d1, h] for h in home for c in cycle for d1 in day if
                              d1 < len(day) - 1), "MaxConsHome")

            model.addConstrs((consHome[c, 0, d2, h] == 0 for c in cycle for d2 in day for h in home if d2 > 0),
                             "MaxConsHome")
            model.addConstrs(
                (consHome[c, d1, d2, h] <= consHome[c, d1 - 1, d2 - 1, h] for c in cycle for d1 in day for d2 in day for
                 h in home if d1 > 0 if d2 > 0), "MaxConsHome")
            model.addConstrs(
                (consHome[c, d1, d2, h] <= n[c, d1, h] for c in cycle for d1 in day for d2 in day for h in home),
                "MaxConsHome")
            model.addConstrs(
                (consHome[c, d1, d2, h] >= n[c, d1, h] + consHome[c, d1 - 1, d2 - 1, h] - 1 for c in cycle for d1 in day
                 for d2 in day for h in home if d1 > 0 if d2 > 0), "MaxConsHome")

            # maximum cons of homegames: applying
            if bounds[34, 5] > 0:
                model.addConstr(
                    (quicksum(
                        consHome[c, d1, d2, h] for c in cycle for d1 in day for d2 in range(bounds[34, 5].astype(int), len(day)) for
                        h in home) == 0), "maxConsHome")
            # skip over minimum consecutive of home games since this is 1 and already deferred from other count constraints

        if bounds[34, 3] + bounds[34, 2] > 0:
            model.addConstrs((consNotHome[c, 0, 0, a] == 1 - n[c, 0, a] for c in cycle for a in away),
                             "MaxAwayTrip")
            model.addConstrs(
                (consNotHome[c, d1 + 1, 0, a] <= n[c, d1, a] for c in cycle for a in away for d1 in day if
                 d1 < len(day) - 1),
                "MaxAwayTrip")
            model.addConstrs(
                (consNotHome[c, d1 + 1, 0, a] <= 1 - n[c, d1 + 1, a] for c in cycle for d1 in day for a in away if
                 d1 < len(day) - 1), "MaxAwayTrip")
            model.addConstrs(
                (consNotHome[c, d1 + 1, 0, a] >= n[c, d1, a] - n[c, d1 + 1, a] for c in cycle for d1 in day for a in
                 away if d1 < len(day) - 1), "MaxAwayTrip")

            model.addConstrs((consNotHome[c, 0, d2, a] == 0 for c in cycle for d2 in day for a in away if d2 > 0))
            model.addConstrs((consNotHome[c, d1, d2, a] <= consNotHome[c, d1 - 1, d2 - 1, a]
                              for c in cycle for d1 in day for d2 in day for a in away if d1 > 0 if d2 > 0),
                             "MaxAwayTrip")
            model.addConstrs((consNotHome[c, d1, d2, a] <= 1 - n[c, d1, a]
                              for c in cycle for d1 in day for d2 in day for a in away if d1 > 0 if d2 > 0),
                             "MaxAwayTrip")
            model.addConstrs((consNotHome[c, d1, d2, a] >= consNotHome[c, d1 - 1, d2 - 1, a] - p[c, d1, a]
                              for c in cycle for d1 in day for d2 in day for a in away if d1 > 0 if d2 > 0),
                             "MaxAwayTrip")
            if bounds[34, 3] > 0:
                model.addConstr(
                    (quicksum(
                        consNotHome[c, d1, d2, a] for c in cycle for d1 in day for d2 in range(bounds[34, 3].astype(int), len(day))
                        for a in away) == 0),
                    "MaxAwayTrip"
                )

        # Sets the number of solutions to be generated
        model.setParam(GRB.Param.PoolSolutions, numSam)
        # grab the most optimal solutions
        model.setParam(GRB.Param.PoolSearchMode, 2)
        model.optimize()
        numSol = model.SolCount
        print("Number of solutions found for the model: " + str(numSol))

        if model.status == GRB.Status.INFEASIBLE:
            model.computeIIS()
            print("Following constraints are infeasible: ")
            for c in model.getConstrs():
                if c.IISConstr:
                    print(c.constrName)
        if model.status == GRB.Status.OPTIMAL:
            model.write('m.sol')
        for i in range(numSol):
            model.setParam(GRB.Param.SolutionNumber, i)
            # get value from subobtimal MIP sol (might change this in X if we dont do soft constraints)
            solution = model.getAttr('xn', x)

            tmp = np.zeros([numCycle, num_md_per_cycle, num_teams, num_teams])
            for key in solution:
                tmp[key] = round(solution[key])
            tmp_sol = tmp.astype(np.int64)
            with open(os.path.join(directory, "sol" + str(i) + ".csv"), "w+", newline='') as sol_csv:
                csv_writer = csv.writer(sol_csv, delimiter=',')

                # writes cycle row
                row = ['']
                for c in range(numCycle):
                    row.extend(['C' + str(c)] * num_md_per_cycle * num_teams)
                csv_writer.writerow(row)

                # writes round row
                row = ['']
                for c in range(numCycle):
                    for d in range(num_md_per_cycle):
                        row.extend(['R' + str(d)] * num_teams)
                csv_writer.writerow(row)

                # writes awayteam row
                row = ['']
                for c in range(numCycle):
                    for d in range(num_md_per_cycle):
                        for t in range(num_teams):
                            row.append('T' + str(t))
                csv_writer.writerow(row)

                # write the actual solution per team
                tmp_sol.astype(int)
                for t in range(num_teams):
                    row = ['T' + str(t)]
                    for c in range(numCycle):
                        for r in range(num_md_per_cycle):
                            for team in range(num_teams):
                                row.append(tmp_sol[c][r][t][team])
                    csv_writer.writerow(row)

    except GurobiError as e:
        raise e


