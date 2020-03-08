import csv
import os

from gurobipy import GurobiError, Model, GRB
import numpy as np

def generate_multi_dim_sample(bounds, directory, num_teams=6, num_md_per_cycle=5, numSam=100, numCycle=2):
    # the list of sample dimensions, the +1
    cycle = list(range(numCycle))
    day = list(range(num_md_per_cycle))
    home = away = list(range(num_teams))

    constrList = [[(0,), (1,)], [(0,), (2,)], [(0,), (3,)], [(0,), (1, 2)], [(0,), (1, 3)], [(0,), (2, 3)],[(0,), (1, 2, 3)],
                  [(1,), (0,)], [(1,), (2,)], [(1,), (3,)], [(1,), (0, 2)], [(1,), (0, 3)],[(1,), (2, 3)],[(1,), (0, 2, 3)],
                  [(2,), (0,)], [(2,), (1,)], [(2,), (3,)], [(2,), (0, 1)],[(2,), (0, 3)], [(2,), (1, 3)], [(2,), (0, 1, 3)],
                  [(3,), (0,)], [(3,), (1,)], [(3,), (2,)], [(3,), (0, 1)], [(3,), (0, 2)], [(3,), (1, 2)],[(3,), (0, 1, 2)],
                  [(0, 1), (2,)], [(0, 1), (3,)], [(0, 1), (2, 3)],
                  [(0, 2), (1,)], [(0, 2), (3,)], [(0, 2), (1, 3)],
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

        ### Hard constraints from bounds files ###
        for i in range(len(bounds)):

            if bounds[i, 0] > 0:
                # this part covers count lowerbound
                print(bounds[i, 0])
                if constrList[i] == [(0,), (1,)]:
                    model.addConstrs((r.sum(c, '*') >= bounds[i, 0] for c in cycle), "constr")
                elif constrList[i] == [(0,), (2,)]:
                    model.addConstrs((t.sum(c, '*') >= bounds[i, 0] for c in cycle), "constr")
                elif constrList[i] == [(0,), (3,)]:
                    model.addConstrs((s.sum(c, '*') >= bounds[i, 0] for c in cycle), "constr")
                elif constrList[i] == [(0,), (1, 2)]:
                    model.addConstrs((n.sum(c, '*', '*') >= bounds[i, 0] for c in cycle), "constr")
                elif constrList[i] == [(0,), (1, 3)]:
                    model.addConstrs((o.sum(c, '*', '*') >= bounds[i, 0] for c in cycle), "constr")
                elif constrList[i] == [(0,), (2, 3)]:
                    model.addConstrs((p.sum(c, '*', '*') >= bounds[i, 0] for c in cycle), "constr")
                elif constrList[i] == [(0,), (1, 2, 3)]:
                    model.addConstrs((x.sum(c, '*', '*', '*') >= bounds[i, 0] for c in cycle), "constr")

                elif constrList[i] == [(1,), (0,)]:
                    model.addConstrs((r.sum('*', d) >= bounds[i, 0] for d in day), "constr")
                elif constrList[i] == [(1,), (2,)]:
                    model.addConstrs((u.sum(d, '*') >= bounds[i, 0] for d in day), "constr")
                elif constrList[i] == [(1,), (3,)]:
                    model.addConstrs((v.sum(d, '*') >= bounds[i, 0] for d in day), "constr")
                elif constrList[i] == [(1,), (0, 2)]:
                    model.addConstrs((n.sum('*', d, '*') >= bounds[i, 0] for d in day), "constr")
                elif constrList[i] == [(1,), (0, 3)]:
                    model.addConstrs((o.sum('*', d, '*') >= bounds[i, 0] for d in day), "constr")
                elif constrList[i] == [(1,), (2, 3)]:
                    model.addConstrs((q.sum(d, '*', '*') >= bounds[i, 0] for d in day), "constr")
                elif constrList[i] == [(1,), (0, 2, 3)]:
                    model.addConstrs((x.sum('*', d, '*', '*') >= bounds[i, 0] for d in day), "constr")

                elif constrList[i] == [(2,), (0,)]:
                    model.addConstrs((t.sum('*', h) >= bounds[i, 0] for h in home), "constr")
                elif constrList[i] == [(2,), (1,)]:
                    model.addConstrs((u.sum('*', h) >= bounds[i, 0] for h in home), "constr")
                elif constrList[i] == [(2,), (3,)]:
                    model.addConstrs((w.sum(h, '*') >= bounds[i, 0] for h in home), "constr")
                elif constrList[i] == [(2,), (0, 1)]:
                    model.addConstrs((n.sum('*', '*', h) >= bounds[i, 0] for h in home), "constr")
                elif constrList[i] == [(2,), (0, 3)]:
                    model.addConstrs((p.sum('*', h, '*') >= bounds[i, 0] for h in home), "constr")
                elif constrList[i] == [(2,), (1, 3)]:
                    model.addConstrs((q.sum('*', h, '*') >= bounds[i, 0] for h in home), "constr")
                elif constrList[i] == [(2,), (0, 1, 3)]:
                    model.addConstrs((x.sum('*', '*', h, '*') >= bounds[i, 0] for h in home), "constr")

                elif constrList[i] == [(3,), (0,)]:
                    model.addConstrs((s.sum('*', a) >= bounds[i, 0] for a in away), "constr")
                elif constrList[i] == [(3,), (1,)]:
                    model.addConstrs((v.sum('*', a) >= bounds[i, 0] for a in away), "constr")
                elif constrList[i] == [(3,), (2,)]:
                    model.addConstrs((w.sum('*', a) >= bounds[i, 0] for a in away), "constr")
                elif constrList[i] == [(3,), (0, 1)]:
                    model.addConstrs((o.sum('*', '*', a) >= bounds[i, 0] for a in away), "constr")
                elif constrList[i] == [(3,), (0, 2)]:
                    model.addConstrs((p.sum('*', '*', a) >= bounds[i, 0] for a in away), "constr")
                elif constrList[i] == [(3,), (1, 2)]:
                    model.addConstrs((q.sum('*', '*', a) >= bounds[i, 0] for a in away), "constr")
                elif constrList[i] == [(3,), (0, 1, 2)]:
                    model.addConstrs((x.sum('*', '*', '*', a) >= bounds[i, 0] for a in away), "constr")

                elif constrList[i] == [(0, 1), (2,)]:
                    model.addConstrs((n.sum(c, d, '*') >= bounds[i, 0] for c in cycle for d in day), "constr")
                elif constrList[i] == [(0, 1), (3,)]:
                    model.addConstrs((o.sum(c, d, '*') >= bounds[i, 0] for c in cycle for d in day), "constr")
                elif constrList[i] == [(0, 1), (2, 3)]:
                    model.addConstrs((x.sum(c, d, '*', '*') >= bounds[i, 0] for c in cycle for d in day), "constr")

                elif constrList[i] == [(0, 2), (1,)]:
                    model.addConstrs((n.sum(c, '*', a) >= bounds[i, 0] for c in cycle for a in away), "constr")
                elif constrList[i] == [(0, 2), (3,)]:
                    model.addConstrs((o.sum(c, '*', a) >= bounds[i, 0] for c in cycle for a in away), "constr")
                elif constrList[i] == [(0, 2), (1, 3)]:
                    model.addConstrs((x.sum(c, '*', a) >= bounds[i, 0] for c in cycle for a in away), "constr")

                elif constrList[i] == [(0, 3), (1,)]:
                    model.addConstrs((n.sum(c, '*', h) >= bounds[i, 0] for c in cycle for h in home), "constr")
                elif constrList[i] == [(0, 3), (2,)]:
                    model.addConstrs((o.sum(c, '*', h) >= bounds[i, 0] for c in cycle for h in home), "constr")
                elif constrList[i] == [(0, 3), (1, 2)]:
                    model.addConstrs((x.sum(c, '*', '*', h) >= bounds[i, 0] for c in cycle for h in home), "constr")

                elif constrList[i] == [(1, 2), (0,)]:
                    model.addConstrs((n.sum('*', d, a) >= bounds[i, 0] for d in day for a in away), "constr")
                elif constrList[i] == [(1, 2), (3,)]:
                    model.addConstrs((o.sum(d, a, '*') >= bounds[i, 0] for d in day for a in away), "constr")
                elif constrList[i] == [(1, 2), (0, 3)]:
                    model.addConstrs((x.sum('*', d, a, '*') >= bounds[i, 0] for d in day for a in away), "constr")

                elif constrList[i] == [(1, 3), (0,)]:
                    model.addConstrs((n.sum('*', d, h) >= bounds[i, 0] for d in day for h in home), "constr")
                elif constrList[i] == [(1, 3), (2,)]:
                    model.addConstrs((o.sum(d, '*', h) >= bounds[i, 0] for d in day for h in home), "constr")
                elif constrList[i] == [(1, 3), (0, 2)]:
                    model.addConstrs((x.sum('*', d, '*',h) >= bounds[i, 0] for d in day for h in home), "constr")

                elif constrList[i] == [(2, 3), (0,)]:
                    model.addConstrs((n.sum('*', h, a) >= bounds[i, 0] for h in home for a in away), "constr")
                elif constrList[i] == [(2, 3), (1,)]:
                    model.addConstrs((o.sum('*', h, a) >= bounds[i, 0] for h in home for a in away), "constr")
                elif constrList[i] == [(2, 3), (0, 1)]:
                    model.addConstrs((x.sum('*', '*', h, a) >= bounds[i, 0] for h in home for a in away), "constr")

                elif constrList[i] == [(0, 1, 2), (3,)]:
                    model.addConstrs((x.sum(c, d, a, '*') >= bounds[i, 0] for c in cycle for d in day for a in away))
                elif constrList[i] == [(0, 1, 3), (2,)]:
                    model.addConstrs((x.sum(c, d, '*', h) >= bounds[i, 0] for c in cycle for d in day for h in home))
                elif constrList[i] == [(0, 2, 3), (1,)]:
                    model.addConstrs((x.sum(c, '*', a, h) >= bounds[i, 0] for c in cycle for a in away for h in home))
                elif constrList[i] == [(1, 2, 3), (0,)]:
                    model.addConstrs((x.sum('*', d, a, h) >= bounds[i, 0] for d in day for a in away for h in home))
            if bounds[i, 1] > 0:
                print(bounds[i, 1])
                if constrList[i] == [(0,), (1,)]:
                    model.addConstrs((r.sum(c, '*') <= bounds[i, 0] for c in cycle), "constr")
                elif constrList[i] == [(0,), (2,)]:
                    model.addConstrs((t.sum(c, '*') <= bounds[i, 0] for c in cycle), "constr")
                elif constrList[i] == [(0,), (3,)]:
                    model.addConstrs((s.sum(c, '*') <= bounds[i, 0] for c in cycle), "constr")
                elif constrList[i] == [(0,), (1, 2)]:
                    model.addConstrs((n.sum(c, '*', '*') <= bounds[i, 0] for c in cycle), "constr")
                elif constrList[i] == [(0,), (1, 3)]:
                    model.addConstrs((o.sum(c, '*', '*') <= bounds[i, 0] for c in cycle), "constr")
                elif constrList[i] == [(0,), (2, 3)]:
                    model.addConstrs((p.sum(c, '*', '*') <= bounds[i, 0] for c in cycle), "constr")
                elif constrList[i] == [(0,), (1, 2, 3)]:
                    model.addConstrs((x.sum(c, '*', '*', '*') <= bounds[i, 0] for c in cycle), "constr")

                elif constrList[i] == [(1,), (0,)]:
                    model.addConstrs((r.sum('*', d) <= bounds[i, 0] for d in day), "constr")
                elif constrList[i] == [(1,), (2,)]:
                    model.addConstrs((u.sum(d, '*') <= bounds[i, 0] for d in day), "constr")
                elif constrList[i] == [(1,), (3,)]:
                    model.addConstrs((v.sum(d, '*') <= bounds[i, 0] for d in day), "constr")
                elif constrList[i] == [(1,), (0, 2)]:
                    model.addConstrs((n.sum('*', d, '*') <= bounds[i, 0] for d in day), "constr")
                elif constrList[i] == [(1,), (0, 3)]:
                    model.addConstrs((o.sum('*', d, '*') <= bounds[i, 0] for d in day), "constr")
                elif constrList[i] == [(1,), (2, 3)]:
                    model.addConstrs((q.sum(d, '*', '*') <= bounds[i, 0] for d in day), "constr")
                elif constrList[i] == [(1,), (0, 2, 3)]:
                    model.addConstrs((x.sum('*', d, '*', '*') <= bounds[i, 0] for d in day), "constr")

                elif constrList[i] == [(2,), (0,)]:
                    model.addConstrs((t.sum('*', h) <= bounds[i, 0] for h in home), "constr")
                elif constrList[i] == [(2,), (1,)]:
                    model.addConstrs((u.sum('*', h) <= bounds[i, 0] for h in home), "constr")
                elif constrList[i] == [(2,), (3,)]:
                    model.addConstrs((w.sum(h, '*') <= bounds[i, 0] for h in home), "constr")
                elif constrList[i] == [(2,), (0, 1)]:
                    model.addConstrs((n.sum('*', '*', h) <= bounds[i, 0] for h in home), "constr")
                elif constrList[i] == [(2,), (0, 3)]:
                    model.addConstrs((p.sum('*', h, '*') <= bounds[i, 0] for h in home), "constr")
                elif constrList[i] == [(2,), (1, 3)]:
                    model.addConstrs((q.sum('*', h, '*') <= bounds[i, 0] for h in home), "constr")
                elif constrList[i] == [(2,), (0, 1, 3)]:
                    model.addConstrs((x.sum('*', '*', h, '*') <= bounds[i, 0] for h in home), "constr")

                elif constrList[i] == [(3,), (0,)]:
                    model.addConstrs((s.sum('*', a) <= bounds[i, 0] for a in away), "constr")
                elif constrList[i] == [(3,), (1,)]:
                    model.addConstrs((v.sum('*', a) <= bounds[i, 0] for a in away), "constr")
                elif constrList[i] == [(3,), (2,)]:
                    model.addConstrs((w.sum('*', a) <= bounds[i, 0] for a in away), "constr")
                elif constrList[i] == [(3,), (0, 1)]:
                    model.addConstrs((o.sum('*', '*', a) <= bounds[i, 0] for a in away), "constr")
                elif constrList[i] == [(3,), (0, 2)]:
                    model.addConstrs((p.sum('*', '*', a) <= bounds[i, 0] for a in away), "constr")
                elif constrList[i] == [(3,), (1, 2)]:
                    model.addConstrs((q.sum('*', '*', a) <= bounds[i, 0] for a in away), "constr")
                elif constrList[i] == [(3,), (0, 1, 2)]:
                    model.addConstrs((x.sum('*', '*', '*', a) <= bounds[i, 0] for a in away), "constr")

                elif constrList[i] == [(0, 1), (2,)]:
                    model.addConstrs((n.sum(c, d, '*') <= bounds[i, 0] for c in cycle for d in day), "constr")
                elif constrList[i] == [(0, 1), (3,)]:
                    model.addConstrs((o.sum(c, d, '*') <= bounds[i, 0] for c in cycle for d in day), "constr")
                elif constrList[i] == [(0, 1), (2, 3)]:
                    model.addConstrs((x.sum(c, d, '*', '*') <= bounds[i, 0] for c in cycle for d in day), "constr")

                elif constrList[i] == [(0, 2), (1,)]:
                    model.addConstrs((n.sum(c, '*', a) <= bounds[i, 0] for c in cycle for a in away), "constr")
                elif constrList[i] == [(0, 2), (3,)]:
                    model.addConstrs((o.sum(c, '*', a) <= bounds[i, 0] for c in cycle for a in away), "constr")
                elif constrList[i] == [(0, 2), (1, 3)]:
                    model.addConstrs((x.sum(c, '*', a) <= bounds[i, 0] for c in cycle for a in away), "constr")

                elif constrList[i] == [(0, 3), (1,)]:
                    model.addConstrs((n.sum(c, '*', h) <= bounds[i, 0] for c in cycle for h in home), "constr")
                elif constrList[i] == [(0, 3), (2,)]:
                    model.addConstrs((o.sum(c, '*', h) <= bounds[i, 0] for c in cycle for h in home), "constr")
                elif constrList[i] == [(0, 3), (1, 2)]:
                    model.addConstrs((x.sum(c, '*', '*', h) <= bounds[i, 0] for c in cycle for h in home), "constr")

                elif constrList[i] == [(1, 2), (0,)]:
                    model.addConstrs((n.sum('*', d, a) <= bounds[i, 0] for d in day for a in away), "constr")
                elif constrList[i] == [(1, 2), (3,)]:
                    model.addConstrs((o.sum(d, a, '*') <= bounds[i, 0] for d in day for a in away), "constr")
                elif constrList[i] == [(1, 2), (0, 3)]:
                    model.addConstrs((x.sum('*', d, a, '*') <= bounds[i, 0] for d in day for a in away), "constr")

                elif constrList[i] == [(1, 3), (0,)]:
                    model.addConstrs((n.sum('*', d, h) <= bounds[i, 0] for d in day for h in home), "constr")
                elif constrList[i] == [(1, 3), (2,)]:
                    model.addConstrs((o.sum(d, '*', h) <= bounds[i, 0] for d in day for h in home), "constr")
                elif constrList[i] == [(1, 3), (0, 2)]:
                    model.addConstrs((x.sum('*', d, '*',h) <= bounds[i, 0] for d in day for h in home), "constr")

                elif constrList[i] == [(2, 3), (0,)]:
                    model.addConstrs((n.sum('*', h, a) <= bounds[i, 0] for h in home for a in away), "constr")
                elif constrList[i] == [(2, 3), (1,)]:
                    model.addConstrs((o.sum('*', h, a) <= bounds[i, 0] for h in home for a in away), "constr")
                elif constrList[i] == [(2, 3), (0, 1)]:
                    model.addConstrs((x.sum('*', '*', h, a) <= bounds[i, 0] for h in home for a in away), "constr")
                elif constrList[i] == [(0, 1, 2), (3,)]:
                    model.addConstrs((x.sum(c, d, a, '*') <= bounds[i, 0] for c in cycle for d in day for a in away))
                elif constrList[i] == [(0, 1, 3), (2,)]:
                    model.addConstrs((x.sum(c, d, '*', h) <= bounds[i, 0] for c in cycle for d in day for h in home))
                elif constrList[i] == [(0, 2, 3), (1,)]:
                    model.addConstrs((x.sum(c, '*', a, h) <= bounds[i, 0] for c in cycle for a in away for h in home))
                elif constrList[i] == [(1, 2, 3), (0,)]:
                    model.addConstrs((x.sum('*', d, a, h) <= bounds[i, 0] for d in day for a in away for h in home))
        # Sets the number of solutions to be generated
        model.setParam(GRB.Param.PoolSolutions,numSam)
        # grab the most optimal solutions
        model.setParam(GRB.Param.PoolSearchMode,2)
        model.optimize()
        numSol = model.SolCount
        print("Number of solutions found for the model: " + str(numSol))

        if model.status == GRB.Status.INFEASIBLE:
            model.computeIIS()
            print("Following constraints are infeasible: ")
            for c in model.getConstrs():
                if c.IISConstr:
                    print('%s',c.constrName)
        if model.status == GRB.Status.OPTIMAL:
            model.write('m.sol')
        model.write('m.sol')
        for i in range(numSol):
            model.setParam(GRB.Param.SolutionNumber,i)
            # get value from subobtimal MIP sol (might change this in X if we dont do soft constraints)
            solution = model.getAttr('xn')
            solution = [int(i) for i in solution]

            tmp = np.zeros([numCycle,num_md_per_cycle,num_teams,num_teams])
            for key in solution:
                tmp[key] = round(solution[key])
            tmp_sol = tmp.astype(np.int64)
            with open(os.path.join(directory,"sol"+str(i)+".csv"),"w+",newline='') as sol_csv:
                csv_writer = csv.writer(sol_csv,delimiter=',')

                # writes cycle row
                row = ['']
                for c in range(numCycle):
                    row.extend(['C'+str(c)]*num_md_per_cycle*num_teams)
                csv_writer.writerow(row)

                # writes round row
                row =['']
                for c in range(numCycle):
                    for d in range(num_md_per_cycle):
                        row.extend(['R'+str(d)]*num_teams)
                csv_writer.writerow(row)

                # writes awayteam row
                row =['']
                for c in range(numCycle):
                    for d in range(num_md_per_cycle):
                        for t in range(num_teams):
                            row.extend('T'+ str(t))

                #write the actual solution per team
                tmp_sol.astype(int)
                for t in range(num_teams):
                    row=['T'+str(t)]
                    for c in range(numCycle):
                        for r in range(num_md_per_cycle):
                            for team in range(num_teams):
                                row.append(tmp_sol[c][r][t][team])
                    csv_writer.writerow(row)

    except GurobiError as e:
        print(str(e))
