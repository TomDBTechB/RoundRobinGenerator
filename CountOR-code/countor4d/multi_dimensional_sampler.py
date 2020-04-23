import csv
import os

from gurobipy import GurobiError, Model, GRB, quicksum
import numpy as np


# run everything to 4d cycle
# learn the model

def generate_multi_dim_sample(bounds, directory, num_teams, num_md_per_cycle, numSam, numCycle,theoretical=False):

    # the list of sample dimensions, the +1
    cycle = list(range(numCycle))
    day = list(range(num_md_per_cycle))
    days = list(range(num_md_per_cycle + 1))
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
    constrListNew = ['tracebounds', 'play_per_day_bounds', 'between_games']
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

        y = model.addVars(cycle, day, home, away, vtype=GRB.BINARY, name="basetrans")
        yn = model.addVars(cycle, day, home, vtype=GRB.BINARY, name="trans_n")

        cNA = model.addVars(cycle, day, day, away, vtype=GRB.BINARY, name="cons")
        cNAs = model.addVars(cycle, days, day, away, vtype=GRB.BINARY, name="cons_min")
        cNH = model.addVars(cycle, day, day, home, vtype=GRB.BINARY, name="consHome")
        cNHs = model.addVars(cycle, days, day, home, vtype=GRB.BINARY, name="consHomes")

        cZy = model.addVars(cycle, day, day, home, vtype=GRB.BINARY, name="days_betw_games")
        cZys = model.addVars(cycle, days, day, home, vtype=GRB.BINARY, name="days_btw_gamess")

        # transpose function
        model.addConstrs(
            y[c, d, h, a] == x[c, d, h, a] + x[c, d, a, h] for c in cycle for d in day for a in away for h in home)
        model.addConstrs((y.sum(c, d, h, '*') == yn[c, d, h] for c in cycle for d in day for h in home), "yn_y")

        model.addConstrs((x.sum(c, d, '*', a) == o[c, d, a] for c in cycle for d in day for a in away), "xo")
        model.addConstrs((x.sum(c, d, h, '*') == n[c, d, h] for c in cycle for d in day for h in home), "xn")
        model.addConstrs((x.sum(c, '*', h, a) == p[c, h, a] for c in cycle for h in home for a in away), "xp")
        model.addConstrs((x.sum('*', d, h, a) == q[d, h, a] for d in day for h in home for a in away), "xq")

        model.addConstrs((r[c, d] <= n.sum(c, d, '*') for c in cycle for d in day), "rn")
        model.addConstrs((t[c, a] <= n.sum(c, '*', a) for c in cycle for a in away), "tn")
        model.addConstrs((v[d, a] <= n.sum('*', d, a) for d in day for a in away), "vn")

        model.addConstrs((r[c, d] <= o.sum(c, d, '*') for c in cycle for d in day), "ro")
        model.addConstrs((s[c, h] <= o.sum(c, '*', h) for c in cycle for h in home), "so")
        model.addConstrs((u[d, h] <= o.sum('*', d, h) for d in day for h in home), "uo")

        model.addConstrs((s[c, h] <= p.sum(c, h, '*') for c in cycle for h in home), "sp")
        model.addConstrs((t[c, a] <= p.sum(c, '*', a) for c in cycle for a in away), "tp")
        model.addConstrs((w[h, a] <= p.sum('*', h, a) for h in home for a in away), "wp")

        model.addConstrs((u[d, h] <= q.sum(d, h, '*') for d in day for h in home), "uq")
        model.addConstrs((v[d, a] <= q.sum(d, '*', a) for d in day for a in away), "vq")
        model.addConstrs((w[h, a] <= q.sum('*', h, a) for h in home for a in away), "wq")

        if theoretical:
             ### Hard constraints -- not yet in bounds ###
             # never play yourself
             model.addConstrs(x[c, d, i, i] == 0 for c in cycle for d in day for i in home)
             # only play one game per day
             model.addConstrs((x.sum(c, d, i, '*') + x.sum(c, d, '*', i) <= 1 for c in cycle for d in day for i in home),
                              "1gamePerDay")

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
                    model.addConstrs((v.sum(d, '*') >= bounds[i, 0] for d in day), "LWR_constr-(1,), (2,)")
                elif constrList[i] == [(1,), (3,)]:
                    model.addConstrs((u.sum(d, '*') >= bounds[i, 0] for d in day), "LWR_constr-(1,), (3,)")
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
                    model.addConstrs((v.sum('*', h) >= bounds[i, 0] for h in home), "LWR_constr-(2,), (1,)")
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
                    model.addConstrs((u.sum('*', a) >= bounds[i, 0] for a in away), "LWR_constr-(3,), (1,)")
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
                    bound = bounds[i, 0]
                    model.addConstrs((o.sum(c, '*', a) >= bounds[i, 0] for c in cycle for a in away),
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
                    model.addConstrs((v.sum(d, '*') <= bounds[i, 1] for d in day), "LWR_constr-(1,), (2,)")
                elif constrList[i] == [(1,), (3,)]:
                    model.addConstrs((u.sum(d, '*') <= bounds[i, 1] for d in day), "LWR_constr-(1,), (3,)")
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
                    model.addConstrs((v.sum('*', h) <= bounds[i, 1] for h in home), "constr-(2,), (1,)")
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
                    model.addConstrs((u.sum('*', a) <= bounds[i, 1] for a in away), "constr-(3,), (1,)")
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
                    model.addConstrs((o.sum(c, '*', a) <= bounds[i, 1] for c in cycle for a in away),
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

        if bounds[20, 5] + bounds[20, 4] > 0:
            # definition for the first day
            model.addConstrs((cNH[c, 0, 0, h] == n[c, 0, h] for c in cycle for h in home), "cNH1")
            model.addConstrs((cNH[c, d1 + 1, 0, h] <= n[c, d1 + 1, h]
                              for c in cycle for h in home for d1 in day
                              if d1 < len(day) - 1), "cNA2")
            model.addConstrs((cNH[c, d1 + 1, 0, h] <= 1 - n[c, d1, h]
                              for c in cycle for h in home for d1 in day
                              if d1 < len(day) - 1), "cNA3")
            model.addConstrs((cNH[c, d1 + 1, 0, h] >= n[c, d1 + 1, h] - n[c, d1, h]
                              for c in cycle for d1 in day for h in home
                              if d1 < len(day) - 1), "cNA4")

            # # definition for the second day and the third, fourth, etc...
            model.addConstrs((cNH[c, 0, d2, h] == 0 for c in cycle for d2 in day for h in home if d2 > 0), "2cNA1")
            model.addConstrs(
                (cNH[c, d1, d2, h] <= cNH[c, d1 - 1, d2 - 1, h] for c in cycle for h in home for d1 in day for d2 in day
                 if d1 > 0 if d2 > 0))
            model.addConstrs(
                (cNH[c, d1, d2, h] <= n[c, d1, h] for c in cycle for d1 in day for d2 in day for h in home if d1 > 0 if
                 d2 > 0))
            model.addConstrs(
                (cNH[c, d1, d2, h] >= n[c, d1, h] + cNH[c, d1 - 1, d2 - 1, h] - 1 for c in cycle for d1 in day for d2 in
                 day for h in home if d1 > 0 if d2 > 0))
            if bounds[20, 5] > 0:
                model.addConstr((quicksum(cNH[c, d1, d2, a] for c in cycle for d1 in day for a in away for d2 in
                                          range(bounds[31, 5].astype(int), len(day))) == 0), "cnASum")
            if bounds[20, 4] > 0:
                model.addConstrs((cNHs[c, 0, d2, h] == 0 for c in cycle for d2 in day for h in home), "minConsPlay")
                model.addConstrs(
                    (cNHs[c, d1, d2, h] <= cNH[c, d1 - 1, d2, h] for c in cycle for h in home for d1 in day for d2 in
                     day if d1 > 0))
                model.addConstrs(
                    (cNHs[c, d1, d2, h] <= 1 - n[c, d1, h] for c in cycle for h in home for d1 in day for d2 in day for
                     h in home if d1 > 0))
                model.addConstrs(
                    (cNHs[c, d1, d2, h] >= cNH[c, d1 - 1, d2, h] - n[c, d1, h] for c in cycle for d1 in day for d2 in
                     day for h in home if d1 > 0))
                model.addConstrs(
                    (cNHs[c, num_md_per_cycle, d2, h] >= cNH[c, num_md_per_cycle - 1, d2, h] for c in cycle for d2 in
                     day for h in home))
                model.addConstr((quicksum(
                    cNHs[c, d1, d2, a] * (bounds[20, 4] - 1 - d2) for c in cycle for a in away for d1 in days for d2 in
                    range(bounds[20, 4].astype(int) - 1)) == 0))

        if bounds[31, 5] + bounds[31, 4] > 0:
            # definition for the first day
            model.addConstrs((cNA[c, 0, 0, a] == o[c, 0, a] for c in cycle for a in away), "cNA1")
            model.addConstrs((cNA[c, d1 + 1, 0, a] <= o[c, d1 + 1, a]
                              for c in cycle for a in away for d1 in day
                              if d1 < len(day) - 1), "cNA2")
            model.addConstrs((cNA[c, d1 + 1, 0, a] <= 1 - o[c, d1, a]
                              for c in cycle for a in away for d1 in day
                              if d1 < len(day) - 1), "cNA3")
            model.addConstrs((cNA[c, d1 + 1, 0, a] >= o[c, d1 + 1, a] - o[c, d1, a]
                              for c in cycle for d1 in day for a in away
                              if d1 < len(day) - 1), "cNA4")

            # # definition for the second day and the third, fourth, etc...
            model.addConstrs((cNA[c, 0, d2, a] == 0 for c in cycle for d2 in day for a in away if d2 > 0), "2cNA1")
            model.addConstrs(
                (cNA[c, d1, d2, a] <= cNA[c, d1 - 1, d2 - 1, a] for c in cycle for a in away for d1 in day for d2 in day
                 if d1 > 0 if d2 > 0))
            model.addConstrs(
                (cNA[c, d1, d2, a] <= o[c, d1, a] for c in cycle for d1 in day for d2 in day for a in away if d1 > 0 if
                 d2 > 0))
            model.addConstrs(
                (cNA[c, d1, d2, a] >= o[c, d1, a] + cNA[c, d1 - 1, d2 - 1, a] - 1 for c in cycle for d1 in day for d2 in
                 day for a in away if d1 > 0 if d2 > 0))
            if bounds[31, 5] > 0:
                model.addConstr((quicksum(cNA[c, d1, d2, a] for c in cycle for d1 in day for a in away for d2 in
                                          range(bounds[31, 5].astype(int), len(day))) == 0), "cnASum")
            if bounds[31, 4] > 0:
                model.addConstrs((cNAs[c, 0, d2, a] == 0 for c in cycle for d2 in day for a in away), "minConsPlay")
                model.addConstrs(
                    (cNAs[c, d1, d2, a] <= cNA[c, d1 - 1, d2, a] for c in cycle for a in away for d1 in day for d2 in
                     day if d1 > 0))
                model.addConstrs(
                    (cNAs[c, d1, d2, a] <= 1 - o[c, d1, a] for c in cycle for d1 in day for d2 in day for a in away if
                     d1 > 0))
                model.addConstrs(
                    (cNAs[c, d1, d2, a] >= cNA[c, d1 - 1, d2, a] - o[c, d1, a] for c in cycle for d1 in day for d2 in
                     day for a in away if d1 > 0))
                model.addConstrs(
                    (cNAs[c, num_md_per_cycle, d2, a] >= cNA[c, num_md_per_cycle - 1, d2, a] for c in cycle for d2 in
                     day for a in away))
                model.addConstr((quicksum(
                    cNAs[c, d1, d2, a] * (bounds[31, 4] - 1 - d2) for c in cycle for a in away for d1 in days for d2 in
                    range(bounds[31, 4].astype(int) - 1)) == 0))

        '''
        for j in range(len(newconst_bounds)):
            if constrListNew[j] == 'tracebounds':
                model.addConstrs((x.sum(c, d, i, i) >= newconst_bounds[j, 0] for c in cycle for d in day for i in home),
                                 "tracelower")
                model.addConstrs((x.sum(c, d, i, i) <= newconst_bounds[j, 1] for c in cycle for d in day for i in home),
                                 "traceupper")
            if constrListNew[j] == 'play_per_day_bounds':
                model.addConstrs(
                    (x.sum(c, d, i, '*') + x.sum(c, d, '*', i) >= newconst_bounds[j, 0] for c in cycle for i in home for
                     d in day), "playlower")
                model.addConstrs(
                    (x.sum(c, d, i, '*') + x.sum(c, d, '*', i) <= newconst_bounds[j, 1] for c in cycle for i in home for
                     d in day), "playupper")
            if constrListNew[j] == 'between_games':
                pass
        if newconst_bounds[2, 1] + newconst_bounds[2, 0] > 0:
            model.addConstrs((cZy[c, 0, 0, h] == 1 - yn[c, 0, h] for c in cycle for h in home))
            model.addConstrs((cZy[c, d1 + 1, 0] <= yn[c, d1, h] for c in cycle for d1 in day for h in home if d1 < len(day) - 1))
            model.addConstrs((cZy[c,d1 + 1,0] <= 1 - yn[c,d1+1,h] for c in cycle for d1 in day for h in home if d1< len(day) - 1))
            model.addConstrs((cZy[c,d1+1,0] >= yn[c,d1,h] - yn[c,d1+1,h] for c in cycle for d1 in day for h in home if d1< len(day) - 1))

            model.addConstrs((cZy[c,0,d2,h] == 0 for c in cycle for h in home for d2 in day if d2>0))
            model.addConstrs((cZy[c,d1,d2,h] <= cZy[c,d1-1,d2-1,h] for c in cycle for d1 in day for d2 in day for h in home if d1>0 if d2>0))
            model.addConstrs((cZy[c,d1,d2,h] <= 1- yn[c,d1,h] for c in cycle for h in home for d1 in day for d2 in day if d1>0 if d2>0))
            model.addConstrs((cZy[c,d1,d2,h] >= cZy[c,d1-1,d2-1,h] - yn[c,d1,h] for c in cycle for h in home for d1 in day for d2 in day if d1>0 if d2>0))

            if newconst_bounds[2,1] > 0:
                model.addConstr((quicksum(cZy[c,d1,d2,h] for c in cycle for h in home for d1 in day for d2 in range(bounds[2,1].astype(int), len(day))) == 0),"test")

            if newconst_bounds[2,0] > 0:
                model.addConstrs(cZys[c,0,d2,h] == 0 for c in cycle for d2 in day for h in home)
                model.addConstrs(cZys[c,d1,d2,h] <= cZy[c,d1-1,d2,h] for c in cycle for h in home for d1 in day for d2 in day if d1>0)
                model.addConstrs(cZys[c,d1,d2,h] <= yn[c,d1,h] for c in cycle for h in home for d1 in day for d2 in day if d1>0)
                model.addConstrs(cZys[c,d1,d2,h] >= cZy[c,d1-1,d2,h] + yn[c,d1,h] - 1 for c in cycle for d1 in day for d2 in day for h in home if d1>0)

                model.addConstr((quicksum(cZys[c,d1,d2,h] * (bounds[2,0] - 1 - d2)
                                         for c in cycle for h in home for d1 in days for d2 in range(bounds[2,0].astype(int) -1))==0),"boundinfo")

        '''


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
