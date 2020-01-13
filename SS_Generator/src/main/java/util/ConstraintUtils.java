package util;

import org.chocosolver.solver.Model;
import org.chocosolver.solver.variables.IntVar;

import java.util.List;

public class ConstraintUtils {

    /**Util methods**/


    /**
     * Seeds the roundRobin tensor with an upper and lowerbound (0-1) booleanwise
     * provide eacht IntVar with unique identifier: e.g the value of 0,0,0 means whether on matchday 0 team 0 played team 0
     *  @param amountOfMatchDays the depth dimension
     * @param model             the model that has the tensor injected
     * @param amountOfTeams
     */
    public static IntVar[][][] seedRobinTensor(int amountOfMatchDays, Model model, int amountOfTeams) {
        IntVar[][][] matchdays = new IntVar[amountOfMatchDays][amountOfTeams][amountOfTeams];
        for (int h = 0; h < amountOfMatchDays; h++) {
            for (int i = 0; i < amountOfTeams; i++) {
                for (int j = 0; j < amountOfTeams; j++) {
                    //every element in the  represents a boolean, 0 and 1, we declare every element in the matrix with a unique combination
                    matchdays[h][i][j] = model.intVar(h + "," + i + "," + j, 0, 1);
                }
            }
        }
        return matchdays;
    }

    public static void prettyPrintSolution(IntVar[][][] matchdays, int amountOfMatchDays, int amountOfTeams) {
        for (int h = 0; h < amountOfMatchDays; h++) {
            System.out.println("matchday " + h);
            IntVar[][] matchday = matchdays[h];
            for (int i = 0; i < amountOfTeams; i++) {
                for (int j = 0; j < amountOfTeams; j++) {
                    System.out.print(matchday[i][j].getValue() + " ");
                }
                System.out.println();

            }

        }
    }

    /**
     * Calculates the amount of games in the round robin tournament
     * @param amountOfTeams
     */
    public static int calculateMatchDays(int amountOfTeams) {
        if (amountOfTeams % 2 == 0)
            return (amountOfTeams - 1) * 2;
        else return amountOfTeams * 2;
    }

    /**
     * Converts a list of IntVar objects to an array of IntVars
     */
    public static IntVar[] convertVarListToArray(List<IntVar> intVarList) {
        IntVar[] intvars = new IntVar[intVarList.size()];
        intvars = intVarList.toArray(intvars);
        return intvars;
    }



}
