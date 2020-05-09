import csv
import os
from datetime import datetime

from gurobipy import GurobiError, Model, GRB, quicksum
import numpy as np


# run everything to 4d cycle
# learn the model

def generate_multi_dim_sample(bounds, directory, num_teams, num_md_per_cycle, numSam, numCycle, unlearnable=False,
                              sk=None, bounds0=None, bounds1=None):
    # the list of sample dimensions, the +1
    cycle = list(range(numCycle))
    day = list(range(num_md_per_cycle))
    days = list(range(num_md_per_cycle + 1))
    home = away = list(range(num_teams))
    sg = list(range(2))

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
        model.setParam(GRB.param.OutputFlag, 1)

        ### Decision Variables ###
        # 0 = cycles, 1 = days, 2 = away, 3 = home
        # regular combinations over the 4 dimensions
        xsg = model.addVars(cycle, day, home, away, sg, vtype=GRB.BINARY, name="basesg")
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

        # transpose function
        model.addConstrs(
            y[c, d, h, a] == x[c, d, h, a] + x[c, d, a, h] for c in cycle for d in day for a in away for h in home)
        model.addConstrs((y.sum(c, d, h, '*') == yn[c, d, h] for c in cycle for d in day for h in home), "yn_y")

        # skillgroup bindings
        model.addConstrs(
            (xsg.sum(c, d, a, h, '*') == x[c, d, a, h] for c in cycle for d in day for a in away for h in home),
            "xo")
        if sk is not None:
            model.addConstrs(
                (xsg[c, d, a, h, skillgr] == x[c, d, a, h] for c in cycle for d in day for a in away for h in home for
                 skillgr
                 in sg if sk[h] == skillgr), "xo")
            model.addConstrs(
                (xsg[c, d, a, h, skillgr] == 0 for c in cycle for d in day for a in away for h in home for skillgr in sg
                 if
                 sk[h] != skillgr), "xo")

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

        # team 1 vs team 2 should happen in the last 2 matchdays of a cycle
        if unlearnable:
            model.addConstrs(x.sum(c, d, 1, 2) <= 1 for c in cycle for d in day if d < len(day) - 2)
            model.addConstrs(x.sum(c, d, 2, 1) <= 1 for c in cycle for d in day if d < len(day) - 2)

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
                    print(str(bounds[i, 0]))
                    model.addConstrs((v.sum(d, '*') >= bounds[i, 0] for d in day), "0LWR_constr-(1,), (2,)")
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
                    model.addConstrs((t.sum('*', a) >= bounds[i, 0] for a in away), "LWR_constr-(2,), (0,)")
                elif constrList[i] == [(2,), (1,)]:
                    model.addConstrs((v.sum('*', a) >= bounds[i, 0] for a in away), "1LWR_constr-(2,), (1,)")
                elif constrList[i] == [(2,), (3,)]:
                    model.addConstrs((w.sum('*', a) >= bounds[i, 0] for a in away), "LWR_constr--(2,), (3,)")
                elif constrList[i] == [(2,), (0, 1)]:
                    model.addConstrs((o.sum('*', '*', a) >= bounds[i, 0] for a in away), "LWR_constr--(2,), (0,1)")
                elif constrList[i] == [(2,), (0, 3)]:
                    model.addConstrs((p.sum('*', '*', a) >= bounds[i, 0] for a in away), "LWR_constr--(2,), (0,3)")
                elif constrList[i] == [(2,), (1, 3)]:
                    model.addConstrs((q.sum('*', '*', a) >= bounds[i, 0] for a in away), "LWR_constr-(2,), (1,3)")
                elif constrList[i] == [(2,), (0, 1, 3)]:
                    model.addConstrs((x.sum('*', '*', '*', a) >= bounds[i, 0] for a in away),
                                     "LWR_constr-(2,), (0,1,3)")

                elif constrList[i] == [(3,), (0,)]:
                    model.addConstrs((s.sum('*', h) >= bounds[i, 0] for h in home), "LWR_constr-(3,), (0,)")
                elif constrList[i] == [(3,), (1,)]:
                    model.addConstrs((u.sum('*', h) >= bounds[i, 0] for h in home), "LWR_constr-(3,), (1,)")
                elif constrList[i] == [(3,), (2,)]:
                    model.addConstrs((w.sum(h, '*') >= bounds[i, 0] for h in home), "LWR_constr-(3,), (2,)")
                elif constrList[i] == [(3,), (0, 1)]:
                    model.addConstrs((n.sum('*', '*', h) >= bounds[i, 0] for h in home), "LWR_constr-(3,), (0,1)")
                elif constrList[i] == [(3,), (0, 2)]:
                    model.addConstrs((p.sum('*', h, '*') >= bounds[i, 0] for h in home), "LWR_constr-(3,), (0,2)")
                elif constrList[i] == [(3,), (1, 2)]:
                    model.addConstrs((q.sum('*', h, '*') >= bounds[i, 0] for h in home), "LWR_constr-(3,), (1,2)")
                elif constrList[i] == [(3,), (0, 1, 2)]:
                    model.addConstrs((x.sum('*', '*', h, '*') >= bounds[i, 0] for h in home),
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
                    model.addConstrs((x.sum(c, d, '*', a) >= bounds[i, 0] for c in cycle for d in day for a in away),
                                     "LWR_constr-(0,1,2), (3,)")
                elif constrList[i] == [(0, 1, 3), (2,)]:
                    model.addConstrs((x.sum(c, d, h, '*') >= bounds[i, 0] for c in cycle for d in day for h in home),
                                     "LWR_constr-(0,1,3), (2,)")
                elif constrList[i] == [(0, 2, 3), (1,)]:
                    model.addConstrs((x.sum(c, '*', h, a) >= bounds[i, 0] for c in cycle for a in away for h in home),
                                     "LWR_constr-(0,2,3), (1,)")
                elif constrList[i] == [(1, 2, 3), (0,)]:
                    model.addConstrs((x.sum('*', d, h, a) >= bounds[i, 0] for d in day for a in away for h in home),
                                     "LWR_constr-(1,2,3), (0,)")
            if bounds[i, 1] > 0:
                # this part covers count lowerbound
                if constrList[i] == [(0,), (1,)]:
                    model.addConstrs((r.sum(c, '*') <= bounds[i, 1] for c in cycle), "LWR_constr-(0,), (1,)")
                elif constrList[i] == [(0,), (2,)]:
                    model.addConstrs((t.sum(c, '*') <= bounds[i, 1] for c in cycle), "LWR_constr-(0,), (2,)")
                elif constrList[i] == [(0,), (3,)]:
                    model.addConstrs((s.sum(c, '*') <= bounds[i, 1] for c in cycle), "LWR_constr-(0,), (3,)")
                elif constrList[i] == [(0,), (1, 2)]:
                    model.addConstrs((o.sum(c, '*', '*') <= bounds[i, 1] for c in cycle), "LWR_constr-(0,), (1,2)")
                elif constrList[i] == [(0,), (1, 3)]:
                    model.addConstrs((n.sum(c, '*', '*') <= bounds[i, 1] for c in cycle), "LWR_constr-(0,), (1,3)")
                elif constrList[i] == [(0,), (2, 3)]:
                    model.addConstrs((p.sum(c, '*', '*') <= bounds[i, 1] for c in cycle), "LWR_constr-(0,), (2,3)")
                elif constrList[i] == [(0,), (1, 2, 3)]:
                    model.addConstrs((x.sum(c, '*', '*', '*') <= bounds[i, 1] for c in cycle),
                                     "LWR_constr-(0,), (1,2,3)")
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
                    model.addConstrs((t.sum('*', a) <= bounds[i, 1] for a in away), "LWR_constr-(2,), (0,)")
                elif constrList[i] == [(2,), (1,)]:
                    model.addConstrs((v.sum('*', a) <= bounds[i, 1] for a in away), "LWR_constr-(2,), (1,)")
                elif constrList[i] == [(2,), (3,)]:
                    model.addConstrs((w.sum('*', a) <= bounds[i, 1] for a in away), "LWR_constr--(2,), (3,)")
                elif constrList[i] == [(2,), (0, 1)]:
                    model.addConstrs((o.sum('*', '*', a) <= bounds[i, 1] for a in away), "LWR_constr--(2,), (0,1)")
                elif constrList[i] == [(2,), (0, 3)]:
                    model.addConstrs((p.sum('*', '*', a) <= bounds[i, 1] for a in away), "LWR_constr--(2,), (0,3)")
                elif constrList[i] == [(2,), (1, 3)]:
                    model.addConstrs((q.sum('*', '*', a) <= bounds[i, 1] for a in away), "LWR_constr-(2,), (1,3)")
                elif constrList[i] == [(2,), (0, 1, 3)]:
                    model.addConstrs((x.sum('*', '*', '*', a) <= bounds[i, 1] for a in away),
                                     "LWR_constr-(2,), (0,1,3)")
                elif constrList[i] == [(3,), (0,)]:
                    model.addConstrs((s.sum('*', h) <= bounds[i, 1] for h in home), "LWR_constr-(3,), (0,)")
                elif constrList[i] == [(3,), (1,)]:
                    model.addConstrs((u.sum('*', h) <= bounds[i, 1] for h in home), "LWR_constr-(3,), (1,)")
                elif constrList[i] == [(3,), (2,)]:
                    model.addConstrs((w.sum(h, '*') <= bounds[i, 1] for h in home), "LWR_constr-(3,), (2,)")
                elif constrList[i] == [(3,), (0, 1)]:
                    model.addConstrs((n.sum('*', '*', h) <= bounds[i, 1] for h in home), "LWR_constr-(3,), (0,1)")
                elif constrList[i] == [(3,), (0, 2)]:
                    model.addConstrs((p.sum('*', h, '*') <= bounds[i, 1] for h in home), "LWR_constr-(3,), (0,2)")
                elif constrList[i] == [(3,), (1, 2)]:
                    model.addConstrs((q.sum('*', h, '*') <= bounds[i, 1] for h in home), "LWR_constr-(3,), (1,2)")
                elif constrList[i] == [(3,), (0, 1, 2)]:
                    model.addConstrs((x.sum('*', '*', h, '*') <= bounds[i, 1] for h in home),
                                     "LWR_constr-(3,), (0,1,2)")
                elif constrList[i] == [(0, 1), (2,)]:
                    model.addConstrs((o.sum(c, d, '*') <= bounds[i, 1] for c in cycle for d in day),
                                     "LWR_constr-(0,1), (2,)")
                elif constrList[i] == [(0, 1), (3,)]:
                    model.addConstrs((n.sum(c, d, '*') <= bounds[i, 1] for c in cycle for d in day),
                                     "LWR_constr-(0,1), (3,)")
                elif constrList[i] == [(0, 1), (2, 3)]:
                    model.addConstrs((x.sum(c, d, '*', '*') <= bounds[i, 1] for c in cycle for d in day),
                                     "LWR_constr-(0,1), (2,3)")
                elif constrList[i] == [(0, 2), (1,)]:
                    bound = bounds[i, 0]
                    model.addConstrs((o.sum(c, '*', a) <= bounds[i, 1] for c in cycle for a in away),
                                     "LWR_constr-(0,2), (1,)")
                elif constrList[i] == [(0, 2), (3,)]:
                    model.addConstrs((p.sum(c, '*', a) <= bounds[i, 1] for c in cycle for a in away),
                                     "LWR_constr-(0,2), (3,)")
                elif constrList[i] == [(0, 2), (1, 3)]:
                    model.addConstrs((x.sum(c, '*', a) <= bounds[i, 1] for c in cycle for a in away),
                                     "LWR_constr-(0,2), (1,3)")
                elif constrList[i] == [(0, 3), (1,)]:
                    model.addConstrs((n.sum(c, '*', h) <= bounds[i, 1] for c in cycle for h in home),
                                     "LWR_constr-(0,3), (1,)")
                elif constrList[i] == [(0, 3), (2,)]:
                    model.addConstrs((p.sum(c, '*', h) <= bounds[i, 1] for c in cycle for h in home),
                                     "LWR_constr-(0,3), (2,)")
                elif constrList[i] == [(0, 3), (1, 2)]:
                    model.addConstrs((x.sum(c, '*', '*', h) <= bounds[i, 1] for c in cycle for h in home),
                                     "LWR_constr-(0,3), (1,2)")
                elif constrList[i] == [(1, 2), (0,)]:
                    model.addConstrs((o.sum('*', d, a) <= bounds[i, 1] for d in day for a in away),
                                     "LWR_constr-(1,2), (0,)")
                elif constrList[i] == [(1, 2), (3,)]:
                    model.addConstrs((q.sum(d, a, '*') <= bounds[i, 1] for d in day for a in away),
                                     "LWR_constr-(1,2), (3,)")
                elif constrList[i] == [(1, 2), (0, 3)]:
                    model.addConstrs((x.sum('*', d, a, '*') <= bounds[i, 1] for d in day for a in away),
                                     "LWR_constr-(1,2), (0,3)")
                elif constrList[i] == [(1, 3), (0,)]:
                    model.addConstrs((n.sum('*', d, h) <= bounds[i, 1] for d in day for h in home),
                                     "LWR_constr-(1,3), (0,)")
                elif constrList[i] == [(1, 3), (2,)]:
                    model.addConstrs((q.sum(d, '*', h) <= bounds[i, 1] for d in day for h in home),
                                     "LWR_constr-(1,3), (2,)")
                elif constrList[i] == [(1, 3), (0, 2)]:
                    model.addConstrs((x.sum('*', d, '*', h) <= bounds[i, 1] for d in day for h in home),
                                     "LWR_constr-(1,3), (0,2)")
                elif constrList[i] == [(2, 3), (0,)]:
                    model.addConstrs((p.sum('*', h, a) <= bounds[i, 1] for h in home for a in away),
                                     "LWR_constr-(2,3), (0,)")
                elif constrList[i] == [(2, 3), (1,)]:
                    model.addConstrs((q.sum('*', h, a) <= bounds[i, 1] for h in home for a in away),
                                     "LWR_constr-(2,3), (1,)")
                elif constrList[i] == [(2, 3), (0, 1)]:
                    model.addConstrs((x.sum('*', '*', h, a) <= bounds[i, 1] for h in home for a in away),
                                     "LWR_constr-(2,3), (0,1)")
                elif constrList[i] == [(0, 1, 2), (3,)]:
                    model.addConstrs((x.sum(c, d, '*', a) <= bounds[i, 1] for c in cycle for d in day for a in away),
                                     "LWR_constr-(0,1,2), (3,)")
                elif constrList[i] == [(0, 1, 3), (2,)]:
                    model.addConstrs((x.sum(c, d, h, '*') <= bounds[i, 1] for c in cycle for d in day for h in home),
                                     "LWR_constr-(0,1,3), (2,)")
                elif constrList[i] == [(0, 2, 3), (1,)]:
                    model.addConstrs((x.sum(c, '*', h, a) <= bounds[i, 1] for c in cycle for a in away for h in home),
                                     "LWR_constr-(0,2,3), (1,)")
                elif constrList[i] == [(1, 2, 3), (0,)]:
                    model.addConstrs((x.sum('*', d, h, a) <= bounds[i, 1] for d in day for a in away for h in home),
                                     "LWR_constr-(1,2,3), (0,)")

            if bounds[i, 6] >= 0:
                if constrList[i] == [(0,), (1, 2, 3)]:
                    model.addConstrs((x.sum(c, '*', t, t) >= bounds[i, 6] for c in cycle for t in home),
                                     "tracing-(0,), (1,2,3)")
                elif constrList[i] == [(1,), (0, 2, 3)]:
                    model.addConstrs((x.sum('*', d, t, t) >= bounds[i, 6] for d in day for t in home),
                                     "tracing (1,), (0,2,3)")
                elif constrList[i] == [(3,), (0, 1, 2)]:
                    model.addConstrs((x.sum('*', '*', a, a) >= bounds[i, 6] for a in away),
                                     "tracing-(3,), (0,1,2)")
                elif constrList[i] == [(0, 1, 2), (3,)]:
                    model.addConstrs((x.sum(c, d, a, a) >= bounds[i, 6] for c in cycle for d in day for a in away),
                                     "tracing-(0,1,2), (3,)")
                elif constrList[i] == [(0, 1, 3), (2,)]:
                    model.addConstrs((x.sum(c, d, h, h) >= bounds[i, 6] for c in cycle for d in day for h in home),
                                     "tracing-(0,1,3), (2,)")
            if bounds[i, 7] >= 0:
                if constrList[i] == [(0,), (1, 2, 3)]:
                    model.addConstrs((x.sum(c, '*', t, t) <= bounds[i, 7] for c in cycle for t in home),
                                     "tracing-(0,), (1,2,3)")
                elif constrList[i] == [(1,), (0, 2, 3)]:
                    model.addConstrs((x.sum('*', d, t, t) >= bounds[i, 7] for d in day for t in home),
                                     "tracing (1,), (0,2,3)")
                elif constrList[i] == [(3,), (0, 1, 2)]:
                    model.addConstrs((x.sum('*', '*', a, a) >= bounds[i, 7] for a in away),
                                     "tracing-(3,), (0,1,2)")
                elif constrList[i] == [(0, 1, 2), (3,)]:
                    model.addConstrs((x.sum(c, d, a, a) >= bounds[i, 7] for c in cycle for d in day for a in away),
                                     "tracing-(0,1,2), (3,)")
                elif constrList[i] == [(0, 1, 3), (2,)]:
                    model.addConstrs((x.sum(c, d, h, h) >= bounds[i, 7] for c in cycle for d in day for h in home),
                                     "tracing-(0,1,3), (2,)")
            if bounds[i, 8] > 0:
                if constrList[i] == [(0, 1, 2), (3,)]:
                    model.addConstrs(
                        (x.sum(c, d, a, '*') + x.sum(c, d, '*', a) >= bounds[i, 8] for c in cycle for d in day for a in
                         away),
                        "LWR_constr-(0,1,2), (3,)")
                elif constrList[i] == [(0, 1, 3), (2,)]:
                    model.addConstrs(
                        (x.sum(c, d, '*', h) + x.sum(c, d, h, '*') >= bounds[i, 8] for c in cycle for d in day for h in
                         home),
                        "LWR_constr-(0,1,3), (2,)")
            if bounds[i, 9] > 0:
                if constrList[i] == [(0, 1, 2), (3,)]:
                    model.addConstrs(
                        (x.sum(c, d, a, '*') + x.sum(c, d, '*', a) <= bounds[i, 9] for c in cycle for d in day for a in
                         away),
                        "LWR_constr-(0,1,2), (3,)")
                elif constrList[i] == [(0, 1, 3), (2,)]:
                    model.addConstrs(
                        (x.sum(c, d, '*', h) + x.sum(c, d, h, '*') <= bounds[i, 9] for c in cycle for d in day for h in
                         home),
                        "LWR_constr-(0,1,3), (2,)")

        if bounds[34, 5] + bounds[34, 4] > 0:
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
            if bounds[34, 5] > 0:
                model.addConstr((quicksum(cNH[c, d1, d2, a] for c in cycle for d1 in day for a in away for d2 in
                                          range(bounds[34, 5].astype(int), len(day))) == 0), "cnASum")
            if bounds[34, 4] > 0:
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
                    cNHs[c, d1, d2, a] * (bounds[34, 4] - 1 - d2) for c in cycle for a in away for d1 in days for d2 in
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

        if sk is not None:
            ### if skill bounds aren't none, we know we have sg0 and sg1 to iterate over
            ### skill group 0
            skill_group0 = [i for i, x in enumerate(sk) if x]
            skill_group1 = [i for i, x in enumerate(sk) if not x]

            o0 = model.addVars(cycle, day, away, vtype=GRB.BINARY, name="o0")
            t0 = model.addVars(cycle, away, vtype=GRB.BINARY, name="t0")
            v0 = model.addVars(day, away, vtype=GRB.BINARY, name="v0")
            r0 = model.addVars(cycle, day, vtype=GRB.BINARY, name="r0")
            model.addConstrs(
                (o0[c, d, a] <= quicksum(x[c, d, h, a] for h in skill_group0) for c in cycle for d in day for a in
                 away),
                "xv0")
            model.addConstrs(
                (r0[c, d] <= o0.sum(c, d, '*') for c in cycle for d in day), "r0o0")
            model.addConstrs(
                (t0[c, a] <= o0.sum(c, '*', a) for c in cycle for a in away), "t0o0")
            model.addConstrs(
                (v0[d,a] <= o0.sum('*',d,a) for d in day for a in away)
            )


            for i in range(len(bounds0)):
                if bounds0[i, 0] > 0:
                    # this part covers count lowerbound
                    if constrList[i] == [(0,), (1,)]:
                        model.addConstrs((r0.sum(c, '*') >= bounds0[i, 0] for c in cycle), "SG0 - LWR_constr-(0,), (1,)")
                    elif constrList[i] == [(0,), (2,)]:
                        model.addConstrs((t0.sum(c, '*') >= bounds0[i, 0] for c in cycle), "SG0 - LWR_constr-(0,), (2,)")
                    elif constrList[i] == [(0,), (3,)]:
                        model.addConstrs((quicksum(s[c, h] for h in skill_group0) >= bounds0[i, 0] for c in cycle),
                                         "SG0 -LWR_constr-(0,), (3,)")
                    elif constrList[i] == [(0,), (1, 2)]:
                        model.addConstrs((o0.sum(c, '*', '*') >= bounds0[i, 0] for c in cycle),
                                         "SG0 -LWR_constr-(0,), (1,2)")
                    elif constrList[i] == [(0,), (1, 3)]:
                        model.addConstrs(
                            (quicksum(n[c, d, h] for h in skill_group0 for d in day) >= bounds0[i, 0] for c in cycle),
                            "SG0 - LWR_constr-(0,), (1,3)")
                    elif constrList[i] == [(0,), (2, 3)]:
                        model.addConstrs(
                            (quicksum(p[c, h, a] for h in skill_group0 for a in away) >= bounds0[i, 0] for c in cycle),
                            "SG0 - LWR_constr-(0,), (2,3)")
                    elif constrList[i] == [(0,), (1, 2, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for d in day for a in away for h in skill_group0) >= bounds0[i, 0]
                             for c in
                             cycle),
                            "SG0 - LWR_constr-(0,), (1,2,3)")

                    elif constrList[i] == [(1,), (0,)]:
                        model.addConstrs((r0.sum('*', d) >= bounds0[i, 0] for d in day), "SG0 - LWR_constr-(1,), (0,)")
                    elif constrList[i] == [(1,), (2,)]:
                        model.addConstrs((v0.sum(d, '*') >= bounds0[i, 0] for d in day), "0SG0 - LWR_constr-(1,), (2,)")
                    elif constrList[i] == [(1,), (3,)]:
                        model.addConstrs((quicksum(u[d, h] for h in skill_group0) >= bounds0[i, 0] for d in day),
                                         "SG0 - LWR_constr-(1,), (3,)")
                    elif constrList[i] == [(1,), (0, 2)]:
                        model.addConstrs((o0.sum('*', d, '*') >= bounds0[i, 0] for d in day),
                                         "SG0 - LWR_constr-(1,), (0,2)")
                    elif constrList[i] == [(1,), (0, 3)]:
                        model.addConstrs(
                            (quicksum(n[c, d, h] for c in cycle for h in skill_group0) >= bounds0[i, 0] for d in day),
                            "SG0 - LWR_constr-(1,), (0,3)")
                    elif constrList[i] == [(1,), (2, 3)]:
                        model.addConstrs(
                            (quicksum(q[d, h, a] for a in away for h in skill_group0) >= bounds0[i, 0] for d in day),
                            "SG0 - LWR_constr-(1,), (2,3)")
                    elif constrList[i] == [(1,), (0, 2, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for c in cycle for a in away for h in skill_group0) >= bounds0[i, 0]
                             for d
                             in day),
                            "SG0 - LWR_constr-(1,), (0,2,3)")

                    elif constrList[i] == [(2,), (0,)]:
                        model.addConstrs((t.sum('*', a) >= bounds0[i, 0] for a in away), "SG0 - LWR_constr-(2,), (0,)")
                    elif constrList[i] == [(2,), (1,)]:
                        model.addConstrs((v.sum('*', a) >= bounds0[i, 0] for a in away), "SG0 - LWR_constr-(2,), (1,)")
                    elif constrList[i] == [(2,), (3,)]:
                        model.addConstrs((quicksum(w[h, a] for h in skill_group0) >= bounds0[i, 0] for a in away),
                                         "SG0 - LWR_constr - (2,), (3,)")
                    elif constrList[i] == [(2,), (0, 1)]:
                        model.addConstrs((o0.sum('*', '*', a) >= bounds0[i, 0] for a in away),
                                         " SG0 - LWR_constr--(2,), (0,1)")
                    elif constrList[i] == [(2,), (0, 3)]:
                        model.addConstrs(
                            (quicksum(p[c, h, a] for h in skill_group0 for c in cycle) >= bounds0[i, 0] for a in away),
                            "SG0 - LWR_constr--(2,), (0,3)")
                    elif constrList[i] == [(2,), (1, 3)]:
                        model.addConstrs(
                            (quicksum(q[d, h, a] for d in day for h in skill_group0) >= bounds0[i, 0] for a in away),
                            "SG0 - LWR_constr-(2,), (1,3)")
                    elif constrList[i] == [(2,), (0, 1, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for c in cycle for d in day for h in skill_group0) >= bounds0[i, 0]
                             for a in
                             away),
                            "SG0 - LWR_constr-(2,), (0,1,3)")

                    elif constrList[i] == [(3,), (0,)]:
                        model.addConstrs((s.sum('*', a) >= bounds0[i, 0] for a in away), "SG0 - LWR_constr-(3,), (0,)")
                    elif constrList[i] == [(3,), (1,)]:
                        model.addConstrs((u.sum('*', a) >= bounds0[i, 0] for a in away), "SG0 - LWR_constr-(3,), (1,)")
                    elif constrList[i] == [(3,), (2,)]:
                        model.addConstrs((w.sum('*', a) >= bounds0[i, 0] for a in away), "SG0 - LWR_constr-(3,), (2,)")
                    elif constrList[i] == [(3,), (0, 1)]:
                        model.addConstrs((n.sum('*', '*', a) >= bounds0[i, 0] for a in away),
                                         "SG0 - LWR_constr-(3,), (0,1)")
                    elif constrList[i] == [(3,), (0, 2)]:
                        model.addConstrs((p.sum('*', '*', a) >= bounds0[i, 0] for a in away),
                                         "SG0 - LWR_constr-(3,), (0,2)")
                    elif constrList[i] == [(3,), (1, 2)]:
                        model.addConstrs((q.sum('*', '*', a) >= bounds0[i, 0] for a in away),
                                         "SG0 - LWR_constr-(3,), (1,2)")
                    elif constrList[i] == [(3,), (0, 1, 2)]:
                        model.addConstrs((x.sum('*', '*', '*', a) >= bounds0[i, 0] for a in away),
                                         "SG0 - LWR_constr-(3,), (0,1,2)")

                    elif constrList[i] == [(0, 1), (2,)]:
                        model.addConstrs((o0.sum(c, d, '*') >= bounds0[i, 0] for c in cycle for d in day),
                                         "SG0 - LWR_constr-(0,1), (2,)")
                    elif constrList[i] == [(0, 1), (3,)]:
                        model.addConstrs(
                            (quicksum(n[c, d, h] for h in skill_group0) >= bounds0[i, 0] for c in cycle for d in day),
                            "SG0 - LWR_constr-(0,1), (3,)")
                    elif constrList[i] == [(0, 1), (2, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for h in skill_group0 for a in away) >= bounds0[i, 0] for c in cycle
                             for d
                             in day),
                            "SG0 - LWR_constr-(0,1), (2,3)")

                    elif constrList[i] == [(0, 2), (1,)]:
                        model.addConstrs((o0.sum(c, '*', a) >= bounds0[i, 0] for c in cycle for a in away),
                                         "SG0 - LWR_constr-(0,2), (1,)")
                    elif constrList[i] == [(0, 2), (3,)]:
                        model.addConstrs(
                            (quicksum(p[c, h, a] for h in skill_group0) >= bounds0[i, 0] for c in cycle for a in away),
                            "SG0 - LWR_constr-(0,2), (3,)")
                    elif constrList[i] == [(0, 2), (1, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for h in skill_group0 for d in day) >= bounds0[i, 0] for c in cycle
                             for a in
                             away),
                            "SG0 - LWR_constr-(0,2), (1,3)")

                    elif constrList[i] == [(0, 3), (1,)]:
                        model.addConstrs((n.sum(c, '*', h) >= bounds0[i, 0] for c in cycle for h in home),
                                         "SG0 - LWR_constr-(0,3), (1,)")
                    elif constrList[i] == [(0, 3), (2,)]:
                        model.addConstrs((p.sum(c, h, '*') >= bounds0[i, 0] for c in cycle for h in home),
                                         "SG0 - LWR_constr-(0,3), (2,)")
                    elif constrList[i] == [(0, 3), (1, 2)]:
                        model.addConstrs((x.sum(c, '*', h, '*') >= bounds0[i, 0] for c in cycle for h in home),
                                         "SG0 - LWR_constr-(0,3), (1,2)")

                    elif constrList[i] == [(1, 2), (0,)]:
                        model.addConstrs((o0.sum('*', d, a) >= bounds0[i, 0] for d in day for a in away),
                                         "SG0 - LWR_constr-(1,2), (0,)")
                    elif constrList[i] == [(1, 2), (3,)]:
                        model.addConstrs(
                            (quicksum(q[d, h, a] for h in skill_group0) >= bounds0[i, 0] for d in day for a in away),
                            "SG0 - LWR_constr-(1,2), (3,)")
                    elif constrList[i] == [(1, 2), (0, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for h in skill_group0 for c in cycle) >= bounds0[i, 0] for d in day
                             for a in
                             away),
                            "SG0 - LWR_constr-(1,2), (0,3)")

                    elif constrList[i] == [(1, 3), (0,)]:
                        model.addConstrs((n.sum('*', d, h) >= bounds0[i, 0] for d in day for h in home),
                                         "SG0 - LWR_constr-(1,3), (0,)")
                    elif constrList[i] == [(1, 3), (2,)]:
                        model.addConstrs((q.sum(d, '*', h) >= bounds0[i, 0] for d in day for h in home),
                                         "SG0 - LWR_constr-(1,3), (2,)")
                    elif constrList[i] == [(1, 3), (0, 2)]:
                        model.addConstrs((x.sum('*', d, '*', h) >= bounds0[i, 0] for d in day for h in home),
                                         "SG0 - LWR_constr-(1,3), (0,2)")

                    elif constrList[i] == [(2, 3), (0,)]:
                        model.addConstrs((p.sum('*', h, a) >= bounds0[i, 0] for h in home for a in away),
                                         "SG0 - LWR_constr-(2,3), (0,)")
                    elif constrList[i] == [(2, 3), (1,)]:
                        model.addConstrs((q.sum('*', h, a) >= bounds0[i, 0] for h in home for a in away),
                                         "SG0 - LWR_constr-(2,3), (1,)")
                    elif constrList[i] == [(2, 3), (0, 1)]:
                        model.addConstrs((x.sum('*', '*', h, a) >= bounds0[i, 0] for h in home for a in away),
                                         "SG0 - LWR_constr-(2,3), (0,1)")

                    elif constrList[i] == [(0, 1, 2), (3,)]:
                        model.addConstrs(
                            (quicksum(x[c, d, a, h] for h in skill_group0) >= bounds0[i, 0] for c in cycle for d in day
                             for a in
                             away),
                            "SG0 - LWR_constr-(0,1,2), (3,)")
                    elif constrList[i] == [(0, 1, 3), (2,)]:
                        model.addConstrs(
                            (x.sum(c, d, '*', h) >= bounds0[i, 0] for c in cycle for d in day for h in home),
                            "SG0 - LWR_constr-(0,1,3), (2,)")
                    elif constrList[i] == [(0, 2, 3), (1,)]:
                        model.addConstrs(
                            (x.sum(c, '*', a, h) >= bounds0[i, 0] for c in cycle for a in away for h in home),
                            "SG0 - LWR_constr-(0,2,3), (1,)")
                    elif constrList[i] == [(1, 2, 3), (0,)]:
                        model.addConstrs(
                            (x.sum('*', d, a, h) >= bounds0[i, 0] for d in day for a in away for h in home),
                            "SG0 - LWR_constr-(1,2,3), (0,)")
                if bounds0[i, 1] > 0:
                    # this part covers count lowerbound
                    if constrList[i] == [(0,), (1,)]:
                        model.addConstrs((r0.sum(c, '*') <= bounds0[i, 1] for c in cycle), "SG0 - LWR_constr-(0,), (1,)")
                    elif constrList[i] == [(0,), (2,)]:
                        model.addConstrs((t0.sum(c, '*') <= bounds0[i, 0] for c in cycle), "SG0 - LWR_constr-(0,), (2,)")
                    elif constrList[i] == [(0,), (3,)]:
                        model.addConstrs((quicksum(s[c, h] for h in skill_group0) <= bounds0[i, 1] for c in cycle),
                                         "SG0 - LWR_constr-(0,), (3,)")
                    elif constrList[i] == [(0,), (1, 2)]:
                        model.addConstrs((o0.sum(c, '*', '*') <= bounds0[i, 1] for c in cycle),
                                         "SG0 - LWR_constr-(0,), (1,2)")
                    elif constrList[i] == [(0,), (1, 3)]:
                        model.addConstrs(
                            (quicksum(n[c, d, h] for h in skill_group0 for d in day) <= bounds0[i, 1] for c in cycle),
                            "SG0 - LWR_constr-(0,), (1,3)")
                    elif constrList[i] == [(0,), (2, 3)]:
                        model.addConstrs(
                            (quicksum(p[c, h, a] for h in skill_group0 for a in away) <= bounds0[i, 1] for c in cycle),
                            "SG0 - LWR_constr-(0,), (2,3)")
                    elif constrList[i] == [(0,), (1, 2, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for d in day for a in away for h in skill_group0) <= bounds0[i, 1]
                             for c in cycle),
                            "SG0 - LWR_constr-(0,), (1,2,3)")
                    elif constrList[i] == [(1,), (0,)]:
                        model.addConstrs((r0.sum('*', d) <= bounds0[i, 1] for d in day), "SG0 - LWR_constr-(1,), (0,)")
                    elif constrList[i] == [(1,), (2,)]:
                        print(str(bounds0[i, 1]))
                        model.addConstrs((v0.sum(d, '*') <= bounds0[i, 1] for d in day), "1SG0 - LWR_constr-(1,), (2,)")
                    elif constrList[i] == [(1,), (3,)]:
                        model.addConstrs((quicksum(u[d, h] for h in skill_group0) <= bounds0[i, 1] for d in day),
                                         "SG0 - LWR_constr-(1,), (3,)")
                    elif constrList[i] == [(1,), (0, 2)]:
                        model.addConstrs((o0.sum('*', d, '*') <= bounds0[i, 1] for d in day),
                                         "SG0 - LWR_constr-(1,), (0,2)")
                    elif constrList[i] == [(1,), (0, 3)]:
                        model.addConstrs(
                            (quicksum(n[c, d, h] for c in cycle for h in skill_group0) <= bounds0[i, 1] for d in day),
                            "SG0 - LWR_constr-(1,), (0,3)")
                    elif constrList[i] == [(1,), (2, 3)]:
                        model.addConstrs(
                            (quicksum(q[d, h, a] for a in away for h in skill_group0) <= bounds0[i, 1] for d in day),
                            "SG0 - LWR_constr-(1,), (2,3)")
                    elif constrList[i] == [(1,), (0, 2, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for c in cycle for a in away for h in skill_group0) <= bounds0[i, 1]
                             for d in day),
                            "SG0 - LWR_constr-(1,), (0,2,3)")
                    elif constrList[i] == [(2,), (0,)]:
                        model.addConstrs((t0.sum('*', a) <= bounds0[i, 1] for a in away), "SG0 - LWR_constr-(2,), (0,)")
                    # todo check fail
                    elif constrList[i] == [(2,), (1,)]:
                        model.addConstrs((v0.sum('*', a) <= bounds0[i, 1] for a in away), "SG0 - LWR_constr-(2,), (1,)")
                    elif constrList[i] == [(2,), (3,)]:
                        model.addConstrs((quicksum(w[h, a] for h in skill_group0) <= bounds0[i, 1] for a in away),
                                         "SG0 - LWR_constr--(2,), (3,)")
                    elif constrList[i] == [(2,), (0, 1)]:
                        model.addConstrs((o0.sum('*', '*', a) <= bounds0[i, 1] for a in away),
                                         "SG0 - LWR_constr--(2,), (0,1)")
                    elif constrList[i] == [(2,), (0, 3)]:
                        model.addConstrs(
                            (quicksum(p[c, h, a] for h in skill_group0 for c in cycle) <= bounds0[i, 1] for a in away),
                            "SG0 - LWR_constr--(2,), (0,3)")
                    elif constrList[i] == [(2,), (1, 3)]:
                        model.addConstrs(
                            (quicksum(q[d, h, a] for d in day for h in skill_group0) <= bounds0[i, 1] for a in away),
                            "SG0 - LWR_constr-(2,), (1,3)")
                    elif constrList[i] == [(2,), (0, 1, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for c in cycle for d in day for h in skill_group0) <= bounds0[i, 1]
                             for a in away),
                            "SG0 - LWR_constr-(2,), (0,1,3)")
                    elif constrList[i] == [(3,), (0,)]:
                        model.addConstrs((s.sum('*', a) <= bounds0[i, 1] for a in away), "SG0 - LWR_constr-(3,), (0,)")
                    elif constrList[i] == [(3,), (1,)]:
                        model.addConstrs((u.sum('*', a) <= bounds0[i, 1] for a in away), "SG0 - LWR_constr-(3,), (1,)")
                    elif constrList[i] == [(3,), (2,)]:
                        model.addConstrs((w.sum('*', a) <= bounds0[i, 1] for a in away), "SG0 - LWR_constr-(3,), (2,)")
                    elif constrList[i] == [(3,), (0, 1)]:
                        model.addConstrs((n.sum('*', '*', a) <= bounds0[i, 1] for a in away),
                                         "SG0 - LWR_constr-(3,), (0,1)")
                    elif constrList[i] == [(3,), (0, 2)]:
                        model.addConstrs((p.sum('*', '*', a) <= bounds0[i, 1] for a in away),
                                         "SG0 - LWR_constr-(3,), (0,2)")
                    elif constrList[i] == [(3,), (1, 2)]:
                        model.addConstrs((q.sum('*', '*', a) <= bounds0[i, 1] for a in away),
                                         "SG0 - LWR_constr-(3,), (1,2)")
                    elif constrList[i] == [(3,), (0, 1, 2)]:
                        model.addConstrs((x.sum('*', '*', '*', a) <= bounds0[i, 1] for a in away),
                                         "SG0 - LWR_constr-(3,), (0,1,2)")
                    elif constrList[i] == [(0, 1), (2,)]:
                        model.addConstrs((o0.sum(c, d, '*') <= bounds0[i, 1] for c in cycle for d in day),
                                         "SG0 - LWR_constr-(0,1), (2,)")
                    elif constrList[i] == [(0, 1), (3,)]:
                        model.addConstrs(
                            (quicksum(n[c, d, h] for h in skill_group0) <= bounds0[i, 1] for c in cycle for d in day),
                            "SG0 - LWR_constr-(0,1), (3,)")
                    elif constrList[i] == [(0, 1), (2, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for h in skill_group0 for a in away) <= bounds0[i, 1] for c in cycle
                             for d in day),
                            "SG0 - LWR_constr-(0,1), (2,3)")
                    elif constrList[i] == [(0, 2), (1,)]:
                        model.addConstrs((o0.sum(c, '*', a) <= bounds0[i, 1] for c in cycle for a in away),
                                         "SG0 - LWR_constr-(0,2), (1,)")
                    elif constrList[i] == [(0, 2), (3,)]:
                        model.addConstrs(
                            (quicksum(p[c, h, a] for h in skill_group0) <= bounds0[i, 1] for c in cycle for a in away),
                            "SG0 - LWR_constr-(0,2), (3,)")
                    elif constrList[i] == [(0, 2), (1, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for h in skill_group0 for d in day) <= bounds0[i, 1] for c in cycle
                             for a in away),
                            "SG0 - LWR_constr-(0,2), (1,3)")
                    elif constrList[i] == [(0, 3), (1,)]:
                        model.addConstrs((n.sum(c, '*', h) <= bounds0[i, 1] for c in cycle for h in home),
                                         "SG0 - LWR_constr-(0,3), (1,)")
                    elif constrList[i] == [(0, 3), (2,)]:
                        model.addConstrs((p.sum(c, h, '*') <= bounds0[i, 1] for c in cycle for h in home),
                                         "SG0 - LWR_constr-(0,3), (2,)")
                    elif constrList[i] == [(0, 3), (1, 2)]:
                        model.addConstrs((x.sum(c, '*', h, '*') <= bounds0[i, 1] for c in cycle for h in home),
                                         "SG0 - LWR_constr-(0,3), (1,2)")
                    elif constrList[i] == [(1, 2), (0,)]:
                        model.addConstrs((o0.sum('*', d, a) <= bounds0[i, 1] for d in day for a in away),
                                         "SG0 - LWR_constr-(1,2), (0,)")
                    elif constrList[i] == [(1, 2), (3,)]:
                        model.addConstrs(
                            (quicksum(q[d, h, a] for h in skill_group0) <= bounds0[i, 1] for d in day for a in away),
                            "SG0 - LWR_constr-(1,2), (3,)")
                    elif constrList[i] == [(1, 2), (0, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for h in skill_group0 for c in cycle) <= bounds0[i, 1] for d in day
                             for a in away),
                            "SG0 - LWR_constr-(1,2), (0,3)")
                    elif constrList[i] == [(1, 3), (0,)]:
                        model.addConstrs((n.sum('*', d, h) <= bounds0[i, 1] for d in day for h in home),
                                         "SG0 - LWR_constr-(1,3), (0,)")
                    elif constrList[i] == [(1, 3), (2,)]:
                        model.addConstrs((q.sum(d, '*', h) <= bounds0[i, 1] for d in day for h in home),
                                         "SG0 - LWR_constr-(1,3), (2,)")
                    elif constrList[i] == [(1, 3), (0, 2)]:
                        model.addConstrs((x.sum('*', d, '*', h) <= bounds0[i, 1] for d in day for h in home),
                                         "SG0 - LWR_constr-(1,3), (0,2)")
                    elif constrList[i] == [(2, 3), (0,)]:
                        model.addConstrs((p.sum('*', h, a) <= bounds0[i, 1] for h in home for a in away),
                                         "SG0 - LWR_constr-(2,3), (0,)")
                    elif constrList[i] == [(2, 3), (1,)]:
                        model.addConstrs((q.sum('*', h, a) <= bounds0[i, 1] for h in home for a in away),
                                         "SG0 - LWR_constr-(2,3), (1,)")
                    elif constrList[i] == [(2, 3), (0, 1)]:
                        model.addConstrs((x.sum('*', '*', h, a) <= bounds0[i, 1] for h in home for a in away),
                                         "SG0 - LWR_constr-(2,3), (0,1)")
                    elif constrList[i] == [(0, 1, 2), (3,)]:
                        model.addConstrs(
                            (quicksum(x[c, d, a, h] for h in skill_group0) <= bounds0[i, 1] for c in cycle for d in day
                             for a in away),
                            "SG0 - LWR_constr-(0,1,2), (3,)")
                    elif constrList[i] == [(0, 1, 3), (2,)]:
                        model.addConstrs(
                            (x.sum(c, d, '*', h) <= bounds0[i, 1] for c in cycle for d in day for h in home),
                            "SG0 - LWR_constr-(0,1,3), (2,)")
                    elif constrList[i] == [(0, 2, 3), (1,)]:
                        model.addConstrs(
                            (x.sum(c, '*', a, h) <= bounds0[i, 1] for c in cycle for a in away for h in home),
                            "SG0 - LWR_constr-(0,2,3), (1,)")
                    elif constrList[i] == [(1, 2, 3), (0,)]:
                        model.addConstrs(
                            (x.sum('*', d, a, h) <= bounds0[i, 1] for d in day for a in away for h in home),
                            "SG0 - LWR_constr-(1,2,3), (0,)")

            cNH0 = model.addVars(cycle, day, day, home, vtype=GRB.BINARY, name="consHome")
            cNHs0 = model.addVars(cycle, days, day, home, vtype=GRB.BINARY, name="consHomes")

            if bounds0[34, 5] + bounds0[34, 4] > 0:
                # definition for the first day
                model.addConstrs((cNH0[c, 0, 0, h] == n[c, 0, h] for c in cycle for h in skill_group0), "cNH1")
                model.addConstrs((cNH0[c, d1 + 1, 0, h] <= n[c, d1 + 1, h]
                                  for c in cycle for h in skill_group0 for d1 in day
                                  if d1 < len(day) - 1), "cNA2")
                model.addConstrs((cNH0[c, d1 + 1, 0, h] <= 1 - n[c, d1, h]
                                  for c in cycle for h in skill_group0 for d1 in day
                                  if d1 < len(day) - 1), "cNA3")
                model.addConstrs((cNH0[c, d1 + 1, 0, h] >= n[c, d1 + 1, h] - n[c, d1, h]
                                  for c in cycle for d1 in day for h in skill_group0
                                  if d1 < len(day) - 1), "cNA4")

                # # definition for the second day and the third, fourth, etc...
                model.addConstrs((cNH0[c, 0, d2, h] == 0 for c in cycle for d2 in day for h in skill_group0 if d2 > 0), "2cNA1")
                model.addConstrs(
                    (cNH0[c, d1, d2, h] <= cNH0[c, d1 - 1, d2 - 1, h] for c in cycle for h in skill_group0 for d1 in day for d2 in
                     day
                     if d1 > 0 if d2 > 0))
                model.addConstrs(
                    (cNH0[c, d1, d2, h] <= n[c, d1, h] for c in cycle for d1 in day for d2 in day for h in
                     skill_group0 if d1 > 0
                     if
                     d2 > 0))
                model.addConstrs(
                    (cNH0[c, d1, d2, h] >= n[c, d1, h] + cNH0[c, d1 - 1, d2 - 1, h] - 1 for c in cycle for d1 in day for
                     d2 in
                     day for h in skill_group0 if d1 > 0 if d2 > 0))
                if bounds0[34, 5] > 0:
                    model.addConstr((quicksum(cNH0[c, d1, d2, h] for c in cycle for d1 in day for h in skill_group0 for d2 in
                                              range(bounds[34, 5].astype(int), len(day))) == 0), "cnASum")
                if bounds[34, 4] > 0:
                    model.addConstrs((cNHs0[c, 0, d2, h] == 0 for c in cycle for d2 in day for h in skill_group0), "minConsPlay")
                    model.addConstrs(
                        (cNHs0[c, d1, d2, h] <= cNH0[c, d1 - 1, d2, h] for c in cycle for h in skill_group0 for d1 in day for d2
                         in
                         day if d1 > 0))
                    model.addConstrs(
                        (cNHs0[c, d1, d2, h] <= 1 - n[c, d1, h] for c in cycle for h in skill_group0 for d1 in day for d2 in day
                         for
                         h in home if d1 > 0))
                    model.addConstrs(
                        (cNHs0[c, d1, d2, h] >= cNH0[c, d1 - 1, d2, h] - n[c, d1, h] for c in cycle for d1 in day for d2
                         in
                         day for h in skill_group0 if d1 > 0))
                    model.addConstrs(
                        (cNHs0[c, num_md_per_cycle, d2, h] >= cNH0[c, num_md_per_cycle - 1, d2, h] for c in cycle for d2
                         in
                         day for h in skill_group0))
                    model.addConstr((quicksum(
                        cNHs0[c, d1, d2, h] * (bounds[34, 4] - 1 - d2) for c in cycle for h in skill_group0 for d1 in days for d2
                        in
                        range(bounds[34, 4].astype(int) - 1)) == 0))





            v1 = model.addVars(day, away, vtype=GRB.BINARY, name="v0")
            o1 = model.addVars(cycle, day, away, vtype=GRB.BINARY, name="o0")
            t1 = model.addVars(cycle, away, vtype=GRB.BINARY, name="t0")
            r1 = model.addVars(cycle, day, vtype=GRB.BINARY, name="v0")
            model.addConstrs(
                (o1[c, d, a] <= quicksum(x[c, d, h, a] for h in skill_group1) for c in cycle for d in day for a in
                 away),
                "xv0")
            model.addConstrs(
                (r1[c, d] <= o1.sum(c, d, '*') for c in cycle for d in day), "r1o1")
            model.addConstrs(
                (t1[c, a] <= o1.sum(c, '*', a) for c in cycle for a in away), "t1o1")
            model.addConstrs(
                (v1[d, a] <= o1.sum('*', d, a) for d in day for a in away), "v1o1")

            for i in range(len(bounds1)):
                if bounds1[i, 0] > 0:
                    # this part covers count lowerbound
                    if constrList[i] == [(0,), (1,)]:
                        model.addConstrs((r1.sum(c, '*') >= bounds1[i, 0] for c in cycle), "SG1 - LWR_constr-(0,), (1,)")
                    elif constrList[i] == [(0,), (2,)]:
                        model.addConstrs((t1.sum(c, '*') >= bounds1[i, 0] for c in cycle), "SG1 - LWR_constr-(0,), (2,)")
                    elif constrList[i] == [(0,), (3,)]:
                        model.addConstrs((quicksum(s[c, h] for h in skill_group1) >= bounds1[i, 0] for c in cycle),
                                         "SG1 - LWR_constr-(0,), (3,)")
                    elif constrList[i] == [(0,), (1, 2)]:
                        model.addConstrs((o1.sum(c, '*', '*') >= bounds1[i, 0] for c in cycle),
                                         "SG1 - LWR_constr-(0,), (1,2)")
                    elif constrList[i] == [(0,), (1, 3)]:
                        model.addConstrs(
                            (quicksum(n[c, d, h] for h in skill_group1 for d in day) >= bounds1[i, 0] for c in cycle),
                            "SG1 - LWR_constr-(0,), (1,3)")
                    elif constrList[i] == [(0,), (2, 3)]:
                        model.addConstrs(
                            (quicksum(p[c, h, a] for h in skill_group1 for a in away) >= bounds1[i, 0] for c in cycle),
                            "SG1 - LWR_constr-(0,), (2,3)")
                    elif constrList[i] == [(0,), (1, 2, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for d in day for a in away for h in skill_group1) >= bounds1[i, 0]
                             for c in
                             cycle),
                            "SG1 - LWR_constr-(0,), (1,2,3)")
                    elif constrList[i] == [(1,), (0,)]:
                        model.addConstrs((r1.sum('*', d) >= bounds1[i, 0] for d in day), "SG1 - LWR_constr-(1,), (0,)")
                    elif constrList[i] == [(1,), (2,)]:
                        model.addConstrs((v1.sum(d, '*') >= bounds1[i, 0] for d in day), "SG1 - LWR_constr-(1,), (2,)")
                    elif constrList[i] == [(1,), (3,)]:
                        model.addConstrs((quicksum(u[d, h] for h in skill_group1) >= bounds1[i, 0] for d in day),
                                         "SG1 - LWR_constr-(1,), (3,)")
                    elif constrList[i] == [(1,), (0, 2)]:
                        model.addConstrs((o1.sum('*', d, '*') >= bounds1[i, 0] for d in day),
                                         "SG1 - LWR_constr-(1,), (0,2)")
                    elif constrList[i] == [(1,), (0, 3)]:
                        model.addConstrs(
                            (quicksum(n[c, d, h] for c in cycle for h in skill_group1) >= bounds1[i, 0] for d in day),
                            "SG1 - LWR_constr-(1,), (0,3)")
                    elif constrList[i] == [(1,), (2, 3)]:
                        model.addConstrs(
                            (quicksum(q[d, h, a] for a in away for h in skill_group1) >= bounds1[i, 0] for d in day),
                            "SG1 - LWR_constr-(1,), (2,3)")
                    elif constrList[i] == [(1,), (0, 2, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for c in cycle for a in away for h in skill_group1) >= bounds1[i, 0]
                             for d
                             in day),
                            "SG1 - LWR_constr-(1,), (0,2,3)")
                    elif constrList[i] == [(2,), (0,)]:
                        model.addConstrs((t1.sum('*', a) >= bounds1[i, 0] for a in away), "SG1 - LWR_constr-(2,), (0,)")
                    elif constrList[i] == [(2,), (1,)]:
                        model.addConstrs((v1.sum('*', a) >= bounds1[i, 0] for a in away), "SG1 - LWR_constr-(2,), (1,)")
                    elif constrList[i] == [(2,), (3,)]:
                        model.addConstrs((quicksum(w[h, a] for h in skill_group1) >= bounds1[i, 0] for a in away),
                                         "SG1 - LWR_constr--(2,), (3,)")
                    elif constrList[i] == [(2,), (0, 1)]:
                        model.addConstrs((o1.sum('*', '*', a) >= bounds1[i, 0] for a in away),
                                         "SG1 - LWR_constr--(2,), (0,1)")
                    elif constrList[i] == [(2,), (0, 3)]:
                        model.addConstrs(
                            (quicksum(p[c, h, a] for h in skill_group1 for c in cycle) >= bounds1[i, 0] for a in away),
                            "SG1 - LWR_constr--(2,), (0,3)")
                    elif constrList[i] == [(2,), (1, 3)]:
                        model.addConstrs(
                            (quicksum(q[d, h, a] for d in day for h in skill_group1) >= bounds1[i, 0] for a in away),
                            "SG1 - LWR_constr-(2,), (1,3)")
                    elif constrList[i] == [(2,), (0, 1, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for c in cycle for d in day for h in skill_group1) >= bounds1[i, 0]
                             for a in
                             away),
                            "SG1 - LWR_constr-(2,), (0,1,3)")
                    elif constrList[i] == [(3,), (0,)]:
                        model.addConstrs((s.sum('*', a) >= bounds1[i, 0] for a in away), "SG1 - LWR_constr-(3,), (0,)")
                    elif constrList[i] == [(3,), (1,)]:
                        model.addConstrs((u.sum('*', a) >= bounds1[i, 0] for a in away), "SG1 - LWR_constr-(3,), (1,)")
                    elif constrList[i] == [(3,), (2,)]:
                        model.addConstrs((w.sum('*', a) >= bounds1[i, 0] for a in away), "SG1 - LWR_constr-(3,), (2,)")
                    elif constrList[i] == [(3,), (0, 1)]:
                        model.addConstrs((n.sum('*', '*', a) >= bounds1[i, 0] for a in away),
                                         "SG1 - LWR_constr-(3,), (0,1)")
                    elif constrList[i] == [(3,), (0, 2)]:
                        model.addConstrs((p.sum('*', '*', a) >= bounds1[i, 0] for a in away),
                                         "SG1 - LWR_constr-(3,), (0,2)")
                    elif constrList[i] == [(3,), (1, 2)]:
                        model.addConstrs((q.sum('*', '*', a) >= bounds1[i, 0] for a in away),
                                         "SG1 - LWR_constr-(3,), (1,2)")
                    elif constrList[i] == [(3,), (0, 1, 2)]:
                        model.addConstrs((x.sum('*', '*', '*', a) >= bounds1[i, 0] for a in away),
                                         "SG1 - LWR_constr-(3,), (0,1,2)")
                    elif constrList[i] == [(0, 1), (2,)]:
                        model.addConstrs((o1.sum(c, d, '*') >= bounds1[i, 0] for c in cycle for d in day),
                                         "SG1 - LWR_constr-(0,1), (2,)")
                    elif constrList[i] == [(0, 1), (3,)]:
                        model.addConstrs(
                            (quicksum(n[c, d, h] for h in skill_group1) >= bounds1[i, 0] for c in cycle for d in day),
                            "SG1 - LWR_constr-(0,1), (3,)")
                    elif constrList[i] == [(0, 1), (2, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for h in skill_group1 for a in away) >= bounds1[i, 0] for c in cycle
                             for d
                             in day),
                            "SG1 - LWR_constr-(0,1), (2,3)")
                    elif constrList[i] == [(0, 2), (1,)]:
                        model.addConstrs((o1.sum(c, '*', a) >= bounds1[i, 0] for c in cycle for a in away),
                                         "SG1 - LWR_constr-(0,2), (1,)")
                    elif constrList[i] == [(0, 2), (3,)]:
                        model.addConstrs(
                            (quicksum(p[c, h, a] for h in skill_group1) >= bounds1[i, 0] for c in cycle for a in away),
                            "SG1 - LWR_constr-(0,2), (3,)")
                    elif constrList[i] == [(0, 2), (1, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for h in skill_group1 for d in day) >= bounds1[i, 0] for c in cycle
                             for a in
                             away),
                            "SG1 - LWR_constr-(0,2), (1,3)")
                    elif constrList[i] == [(0, 3), (1,)]:
                        model.addConstrs((n.sum(c, '*', h) >= bounds1[i, 0] for c in cycle for h in home),
                                         "SG1 - LWR_constr-(0,3), (1,)")
                    elif constrList[i] == [(0, 3), (2,)]:
                        model.addConstrs((p.sum(c, h, '*') >= bounds1[i, 0] for c in cycle for h in home),
                                         "SG1 - LWR_constr-(0,3), (2,)")
                    elif constrList[i] == [(0, 3), (1, 2)]:
                        model.addConstrs((x.sum(c, '*', h, '*') >= bounds1[i, 0] for c in cycle for h in home),
                                         "SG1 - LWR_constr-(0,3), (1,2)")
                    elif constrList[i] == [(1, 2), (0,)]:
                        model.addConstrs((o1.sum('*', d, a) >= bounds1[i, 0] for d in day for a in away),
                                         "SG1 - LWR_constr-(1,2), (0,)")
                    elif constrList[i] == [(1, 2), (3,)]:
                        model.addConstrs(
                            (quicksum(q[d, h, a] for h in skill_group1) >= bounds1[i, 0] for d in day for a in away),
                            "SG1 - LWR_constr-(1,2), (3,)")
                    elif constrList[i] == [(1, 2), (0, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for h in skill_group1 for c in cycle) >= bounds1[i, 0] for d in day
                             for a in
                             away),
                            "SG1 - LWR_constr-(1,2), (0,3)")
                    elif constrList[i] == [(1, 3), (0,)]:
                        model.addConstrs((n.sum('*', d, h) >= bounds1[i, 0] for d in day for h in home),
                                         "SG1 - LWR_constr-(1,3), (0,)")
                    elif constrList[i] == [(1, 3), (2,)]:
                        model.addConstrs((q.sum(d, '*', h) >= bounds1[i, 0] for d in day for h in home),
                                         "SG1 - LWR_constr-(1,3), (2,)")
                    elif constrList[i] == [(1, 3), (0, 2)]:
                        model.addConstrs((x.sum('*', d, '*', h) >= bounds1[i, 0] for d in day for h in home),
                                         "SG1 - LWR_constr-(1,3), (0,2)")
                    elif constrList[i] == [(2, 3), (0,)]:
                        model.addConstrs((p.sum('*', h, a) >= bounds1[i, 0] for h in home for a in away),
                                         "SG1 - LWR_constr-(2,3), (0,)")
                    elif constrList[i] == [(2, 3), (1,)]:
                        model.addConstrs((q.sum('*', h, a) >= bounds1[i, 0] for h in home for a in away),
                                         "SG1 - LWR_constr-(2,3), (1,)")
                    elif constrList[i] == [(2, 3), (0, 1)]:
                        model.addConstrs((x.sum('*', '*', h, a) >= bounds1[i, 0] for h in home for a in away),
                                         "SG1 - LWR_constr-(2,3), (0,1)")
                    elif constrList[i] == [(0, 1, 2), (3,)]:
                        model.addConstrs(
                            (quicksum(x[c, d, a, h] for h in skill_group1) >= bounds1[i, 0] for c in cycle for d in day
                             for a in
                             away),
                            "SG1 - LWR_constr-(0,1,2), (3,)")
                    elif constrList[i] == [(0, 1, 3), (2,)]:
                        model.addConstrs(
                            (x.sum(c, d, '*', h) >= bounds1[i, 0] for c in cycle for d in day for h in home),
                            "SG1 - LWR_constr-(0,1,3), (2,)")
                    elif constrList[i] == [(0, 2, 3), (1,)]:
                        model.addConstrs(
                            (x.sum(c, '*', a, h) >= bounds1[i, 0] for c in cycle for a in away for h in home),
                            "SG1 - LWR_constr-(0,2,3), (1,)")
                    elif constrList[i] == [(1, 2, 3), (0,)]:
                        model.addConstrs(
                            (x.sum('*', d, a, h) >= bounds1[i, 0] for d in day for a in away for h in home),
                            "SG1 - LWR_constr-(1,2,3), (0,)")
                if bounds1[i, 1] > 0:
                    # this part covers count lowerbound
                    if constrList[i] == [(0,), (1,)]:
                        model.addConstrs((r1.sum(c, '*') <= bounds1[i, 1] for c in cycle),
                                         "SG0 - SG1 - LWR_constr-(0,), (1,)")
                    elif constrList[i] == [(0,), (2,)]:
                        model.addConstrs((t1.sum(c, '*') <= bounds1[i, 0] for c in cycle), "SG1 - LWR_constr-(0,), (2,)")
                    elif constrList[i] == [(0,), (3,)]:
                        model.addConstrs((quicksum(s[c, h] for h in skill_group1) <= bounds1[i, 1] for c in cycle),
                                         "SG1 - LWR_constr-(0,), (3,)")
                    elif constrList[i] == [(0,), (1, 2)]:
                        model.addConstrs((o1.sum(c, '*', '*') <= bounds1[i, 1] for c in cycle),
                                         "SG1 - LWR_constr-(0,), (1,2)")
                    elif constrList[i] == [(0,), (1, 3)]:
                        model.addConstrs(
                            (quicksum(n[c, d, h] for h in skill_group1 for d in day) <= bounds1[i, 1] for c in cycle),
                            "SG1 - LWR_constr-(0,), (1,3)")
                    elif constrList[i] == [(0,), (2, 3)]:
                        model.addConstrs(
                            (quicksum(p[c, h, a] for h in skill_group1 for a in away) <= bounds1[i, 1] for c in cycle),
                            "SG1 - LWR_constr-(0,), (2,3)")
                    elif constrList[i] == [(0,), (1, 2, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for d in day for a in away for h in skill_group1) <= bounds1[i, 1]
                             for c in cycle),
                            "SG1 - LWR_constr-(0,), (1,2,3)")
                    elif constrList[i] == [(1,), (0,)]:
                        model.addConstrs((r1.sum('*', d) <= bounds1[i, 1] for d in day), "SG1 - LWR_constr-(1,), (0,)")
                    elif constrList[i] == [(1,), (2,)]:
                        model.addConstrs((v1.sum(d, '*') <= bounds1[i, 1] for d in day), "SG1 - LWR_constr-(1,), (2,)")
                    elif constrList[i] == [(1,), (3,)]:
                        model.addConstrs((quicksum(u[d, h] for h in skill_group1) <= bounds1[i, 1] for d in day),
                                         "SG1 - LWR_constr-(1,), (3,)")
                    elif constrList[i] == [(1,), (0, 2)]:
                        model.addConstrs((o1.sum('*', d, '*') <= bounds1[i, 1] for d in day),
                                         "SG1 - LWR_constr-(1,), (0,2)")
                    elif constrList[i] == [(1,), (0, 3)]:
                        model.addConstrs(
                            (quicksum(n[c, d, h] for c in cycle for h in skill_group1) <= bounds1[i, 1] for d in day),
                            "SG1 - LWR_constr-(1,), (0,3)")
                    elif constrList[i] == [(1,), (2, 3)]:
                        model.addConstrs(
                            (quicksum(q[d, h, a] for a in away for h in skill_group1) <= bounds1[i, 1] for d in day),
                            "SG1 - LWR_constr-(1,), (2,3)")
                    elif constrList[i] == [(1,), (0, 2, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for c in cycle for a in away for h in skill_group1) <= bounds1[i, 1]
                             for d in day),
                            "SG1 - LWR_constr-(1,), (0,2,3)")
                    elif constrList[i] == [(2,), (0,)]:
                        model.addConstrs((t0.sum('*', a) <= bounds1[i, 1] for a in away), "SG1 - LWR_constr-(2,), (0,)")
                    elif constrList[i] == [(2,), (1,)]:
                        model.addConstrs((v1.sum('*', a) <= bounds1[i, 1] for a in away), "SG1 - LWR_constr-(2,), (1,)")
                    elif constrList[i] == [(2,), (3,)]:
                        model.addConstrs((quicksum(w[h, a] for h in skill_group1) <= bounds1[i, 1] for a in away),
                                         "SG1 - LWR_constr--(2,), (3,)")
                    elif constrList[i] == [(2,), (0, 1)]:
                        model.addConstrs((o1.sum('*', '*', a) <= bounds1[i, 1] for a in away),
                                         "SG1 - LWR_constr--(2,), (0,1)")
                    elif constrList[i] == [(2,), (0, 3)]:
                        model.addConstrs(
                            (quicksum(p[c, h, a] for h in skill_group1 for c in cycle) <= bounds1[i, 1] for a in away),
                            "SG1 - LWR_constr--(2,), (0,3)")
                    elif constrList[i] == [(2,), (1, 3)]:
                        model.addConstrs(
                            (quicksum(q[d, h, a] for d in day for h in skill_group1) <= bounds1[i, 1] for a in away),
                            "SG1 - LWR_constr-(2,), (1,3)")
                    elif constrList[i] == [(2,), (0, 1, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for c in cycle for d in day for h in skill_group1) <= bounds1[i, 1]
                             for a in away),
                            "SG1 - LWR_constr-(2,), (0,1,3)")
                    elif constrList[i] == [(3,), (0,)]:
                        model.addConstrs((s.sum('*', a) <= bounds1[i, 1] for a in away), "SG1 - LWR_constr-(3,), (0,)")
                    elif constrList[i] == [(3,), (1,)]:
                        model.addConstrs((u.sum('*', a) <= bounds1[i, 1] for a in away), "SG1 - LWR_constr-(3,), (1,)")
                    elif constrList[i] == [(3,), (2,)]:
                        model.addConstrs((w.sum('*', a) <= bounds1[i, 1] for a in away), "SG1 - LWR_constr-(3,), (2,)")
                    elif constrList[i] == [(3,), (0, 1)]:
                        model.addConstrs((n.sum('*', '*', a) <= bounds1[i, 1] for a in away),
                                         "SG1 - LWR_constr-(3,), (0,1)")
                    elif constrList[i] == [(3,), (0, 2)]:
                        model.addConstrs((p.sum('*', '*', a) <= bounds1[i, 1] for a in away),
                                         "SG1 - LWR_constr-(3,), (0,2)")
                    elif constrList[i] == [(3,), (1, 2)]:
                        model.addConstrs((q.sum('*', '*', a) <= bounds1[i, 1] for a in away),
                                         "SG1 - LWR_constr-(3,), (1,2)")
                    elif constrList[i] == [(3,), (0, 1, 2)]:
                        model.addConstrs((x.sum('*', '*', '*', a) <= bounds1[i, 1] for a in away),
                                         "SG1 - LWR_constr-(3,), (0,1,2)")
                    elif constrList[i] == [(0, 1), (2,)]:
                        model.addConstrs((o1.sum(c, d, '*') <= bounds1[i, 1] for c in cycle for d in day),
                                         "SG1 - LWR_constr-(0,1), (2,)")
                    elif constrList[i] == [(0, 1), (3,)]:
                        model.addConstrs(
                            (quicksum(n[c, d, h] for h in skill_group1) <= bounds1[i, 1] for c in cycle for d in day),
                            "SG1 - LWR_constr-(0,1), (3,)")
                    elif constrList[i] == [(0, 1), (2, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for h in skill_group1 for a in away) <= bounds1[i, 1] for c in cycle
                             for d in day),
                            "SG1 - LWR_constr-(0,1), (2,3)")
                    elif constrList[i] == [(0, 2), (1,)]:
                        model.addConstrs((o1.sum(c, '*', a) <= bounds1[i, 1] for c in cycle for a in away),
                                         "SG1 - LWR_constr-(0,2), (1,)")
                    elif constrList[i] == [(0, 2), (3,)]:
                        model.addConstrs(
                            (quicksum(p[c, h, a] for h in skill_group1) <= bounds1[i, 1] for c in cycle for a in away),
                            "SG1 - LWR_constr-(0,2), (3,)")
                    elif constrList[i] == [(0, 2), (1, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for h in skill_group1 for d in day) <= bounds1[i, 1] for c in cycle
                             for a in away),
                            "SG1 - LWR_constr-(0,2), (1,3)")
                    elif constrList[i] == [(0, 3), (1,)]:
                        model.addConstrs((n.sum(c, '*', h) <= bounds1[i, 1] for c in cycle for h in home),
                                         "SG1 - LWR_constr-(0,3), (1,)")
                    elif constrList[i] == [(0, 3), (2,)]:
                        model.addConstrs((p.sum(c, h, '*') <= bounds1[i, 1] for c in cycle for h in home),
                                         "SG1 - LWR_constr-(0,3), (2,)")
                    elif constrList[i] == [(0, 3), (1, 2)]:
                        model.addConstrs((x.sum(c, '*', h, '*') <= bounds1[i, 1] for c in cycle for h in home),
                                         "SG1 - LWR_constr-(0,3), (1,2)")
                    elif constrList[i] == [(1, 2), (0,)]:
                        model.addConstrs((o1.sum('*', d, a) <= bounds1[i, 1] for d in day for a in away),
                                         "SG1 - LWR_constr-(1,2), (0,)")
                    elif constrList[i] == [(1, 2), (3,)]:
                        model.addConstrs(
                            (quicksum(q[d, h, a] for h in skill_group1) <= bounds1[i, 1] for d in day for a in away),
                            "SG1 - LWR_constr-(1,2), (3,)")
                    elif constrList[i] == [(1, 2), (0, 3)]:
                        model.addConstrs(
                            (quicksum(x[c, d, h, a] for h in skill_group1 for c in cycle) <= bounds1[i, 1] for d in day
                             for a in away),
                            "SG1 - LWR_constr-(1,2), (0,3)")
                    elif constrList[i] == [(1, 3), (0,)]:
                        model.addConstrs((n.sum('*', d, h) <= bounds1[i, 1] for d in day for h in home),
                                         "SG1 - LWR_constr-(1,3), (0,)")
                    elif constrList[i] == [(1, 3), (2,)]:
                        model.addConstrs((q.sum(d, '*', h) <= bounds1[i, 1] for d in day for h in home),
                                         "SG1 - LWR_constr-(1,3), (2,)")
                    elif constrList[i] == [(1, 3), (0, 2)]:
                        model.addConstrs((x.sum('*', d, '*', h) <= bounds1[i, 1] for d in day for h in home),
                                         "SG1 - LWR_constr-(1,3), (0,2)")
                    elif constrList[i] == [(2, 3), (0,)]:
                        model.addConstrs((p.sum('*', h, a) <= bounds1[i, 1] for h in home for a in away),
                                         "SG1 - LWR_constr-(2,3), (0,)")
                    elif constrList[i] == [(2, 3), (1,)]:
                        model.addConstrs((q.sum('*', h, a) <= bounds1[i, 1] for h in home for a in away),
                                         "SG1 - LWR_constr-(2,3), (1,)")
                    elif constrList[i] == [(2, 3), (0, 1)]:
                        model.addConstrs((x.sum('*', '*', h, a) <= bounds1[i, 1] for h in home for a in away),
                                         "SG1 - LWR_constr-(2,3), (0,1)")
                    elif constrList[i] == [(0, 1, 2), (3,)]:
                        model.addConstrs(
                            (quicksum(x[c, d, a, h] for h in skill_group1) <= bounds1[i, 1] for c in cycle for d in day
                             for a in away),
                            "SG1 - LWR_constr-(0,1,2), (3,)")
                    elif constrList[i] == [(0, 1, 3), (2,)]:
                        model.addConstrs(
                            (x.sum(c, d, '*', h) <= bounds1[i, 1] for c in cycle for d in day for h in home),
                            "SG1 - LWR_constr-(0,1,3), (2,)")
                    elif constrList[i] == [(0, 2, 3), (1,)]:
                        model.addConstrs(
                            (x.sum(c, '*', a, h) <= bounds1[i, 1] for c in cycle for a in away for h in home),
                            "SG1 - LWR_constr-(0,2,3), (1,)")
                    elif constrList[i] == [(1, 2, 3), (0,)]:
                        model.addConstrs(
                            (x.sum('*', d, a, h) <= bounds1[i, 1] for d in day for a in away for h in home),
                            "SG1 - LWR_constr-(1,2,3), (0,)")

            cNH1 = model.addVars(cycle, day, day, home, vtype=GRB.BINARY, name="consHome")
            cNHs1 = model.addVars(cycle, days, day, home, vtype=GRB.BINARY, name="consHomes")

            if bounds1[34, 5] + bounds1[34, 4] > 0:
                # definition for the first day
                model.addConstrs((cNH1[c, 0, 0, h] == n[c, 0, h] for c in cycle for h in skill_group1), "cNH1")
                model.addConstrs((cNH1[c, d1 + 1, 0, h] <= n[c, d1 + 1, h]
                                  for c in cycle for h in skill_group1 for d1 in day
                                  if d1 < len(day) - 1), "cNA2")
                model.addConstrs((cNH1[c, d1 + 1, 0, h] <= 1 - n[c, d1, h]
                                  for c in cycle for h in skill_group1 for d1 in day
                                  if d1 < len(day) - 1), "cNA3")
                model.addConstrs((cNH1[c, d1 + 1, 0, h] >= n[c, d1 + 1, h] - n[c, d1, h]
                                  for c in cycle for d1 in day for h in skill_group1
                                  if d1 < len(day) - 1), "cNA4")

                # # definition for the second day and the third, fourth, etc...
                model.addConstrs((cNH1[c, 0, d2, h] == 0 for c in cycle for d2 in day for h in skill_group1 if d2 > 0), "2cNA1")
                model.addConstrs(
                    (cNH1[c, d1, d2, h] <= cNH1[c, d1 - 1, d2 - 1, h] for c in cycle for h in skill_group1 for d1 in day for d2 in
                     day
                     if d1 > 0 if d2 > 0))
                model.addConstrs(
                    (cNH1[c, d1, d2, h] <= n[c, d1, h] for c in cycle for d1 in day for d2 in day for h in
                     skill_group1 if d1 > 0
                     if
                     d2 > 0))
                model.addConstrs(
                    (cNH1[c, d1, d2, h] >= n[c, d1, h] + cNH1[c, d1 - 1, d2 - 1, h] - 1 for c in cycle for d1 in day for
                     d2 in
                     day for h in skill_group1 if d1 > 0 if d2 > 0))
                if bounds0[34, 5] > 0:
                    model.addConstr((quicksum(cNH1[c, d1, d2, h] for c in cycle for d1 in day for h in skill_group1 for d2 in
                                              range(bounds[34, 5].astype(int), len(day))) == 0), "cnASum")
                if bounds[34, 4] > 0:
                    model.addConstrs((cNHs1[c, 0, d2, h] == 0 for c in cycle for d2 in day for h in skill_group1), "minConsPlay")
                    model.addConstrs(
                        (cNHs1[c, d1, d2, h] <= cNH1[c, d1 - 1, d2, h] for c in cycle for h in skill_group1 for d1 in day for d2
                         in
                         day if d1 > 0))
                    model.addConstrs(
                        (cNHs1[c, d1, d2, h] <= 1 - n[c, d1, h] for c in cycle for h in skill_group1 for d1 in day for d2 in day
                         if d1 > 0))
                    model.addConstrs(
                        (cNHs1[c, d1, d2, h] >= cNH1[c, d1 - 1, d2, h] - n[c, d1, h] for c in cycle for d1 in day for d2
                         in
                         day for h in skill_group1 if d1 > 0))
                    model.addConstrs(
                        (cNHs1[c, num_md_per_cycle, d2, h] >= cNH1[c, num_md_per_cycle - 1, d2, h] for c in cycle for d2
                         in
                         day for h in skill_group1))
                    model.addConstr((quicksum(
                        cNHs1[c, d1, d2, h] * (bounds[34, 4] - 1 - d2) for c in cycle for h in skill_group1 for d1 in days for d2
                        in
                        range(bounds[34, 4].astype(int) - 1)) == 0))


        # Sets the number of solutions to be generated
        model.setParam(GRB.Param.PoolSolutions, numSam)
        # grab the most optimal solutions
        model.setParam(GRB.Param.PoolSearchMode, 2)
        print("Entering model.optimize at {time}".format(time=datetime.now()))
        model.optimize()
        print("Exiting model.optimize at {time}".format(time=datetime.now()))

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
