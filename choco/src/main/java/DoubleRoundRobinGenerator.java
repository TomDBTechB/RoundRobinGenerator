import org.apache.commons.lang3.time.StopWatch;
import org.chocosolver.solver.Model;
import org.chocosolver.solver.variables.IntVar;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public class DoubleRoundRobinGenerator {


    public static void main(String[] args) {
        int amountOfTeams = 6; //Integer.parseInt(args[0]);
        int amountOfSamples = 1; //Integer.parseInt(args[1]);
        //String sampleDirectory = args[2];
        StopWatch watch = new StopWatch();
        watch.start();
        int amountOfMatchDays = calculateMatchDays(amountOfTeams);


        //modelgenerator is used for any problem
        Model model = new Model("xRoundRobinGenerator");
        IntVar[][][] matchdays = new IntVar[amountOfMatchDays][amountOfTeams][amountOfTeams];
        //seed the tensor with variables
        seedRobinTensor(amountOfMatchDays, model, matchdays, amountOfTeams);
        watch.split();
        System.out.println("seed after " + watch.getSplitTime());
        //constraint 1: A team never plays itself
        addNeverPlayYourselfConst(amountOfMatchDays, model, matchdays, amountOfTeams);
        watch.split();
        System.out.println("never Play yourself after " + watch.getSplitTime());
        //constraint 2: A team can only play one game each matchday
        playMaxOneGamePerMatchday(amountOfMatchDays, model, matchdays, amountOfTeams);
        watch.split();
        System.out.println("play one each matchday " + watch.getSplitTime());
        //constraint 3: After the full tournament, every team has played every team twice
        everyonePlaysEachoterTwice(amountOfMatchDays, model, matchdays, amountOfTeams);
        //constraint 4: At the halfway point, each team should have played every team once (general rule, after amountOfMatchdays/2 for all n)
        watch.split();
        System.out.println("Play eachother twice " + watch.getSplitTime());
        halfWayPointConstraint(amountOfMatchDays, matchdays, model, amountOfTeams);
        watch.split();
        System.out.println("Amount of matchdays " + watch.getSplitTime());
        //constraint 5: Optimization of the home and away pattern
        //homeAndAwayPattern(amountOfMatchDays,matchdays,model);


        //MiniZinc black magic
        int counter = 0;
        model.getSolver().limitSolution(10);
        while (model.getSolver().solve()&& counter<amountOfSamples) {
            prettyPrintSolution(matchdays, amountOfMatchDays, amountOfTeams);
            CsvWriter.createSample(matchdays,amountOfMatchDays,amountOfTeams,counter);
            counter++;
        }
        System.out.println("Amount of valid solutions for " + amountOfTeams + " teams: " + counter);

    }




    private static void everyonePlaysEachoterTwice(int amountOfMatchDays, Model model, IntVar[][][] matchdays, int amountOfTeams) {
        for (int i = 0; i < amountOfTeams; i++) {
            for (int j = 0; j < amountOfTeams; j++) {
                if (i != j) {

                    //grab element (i,j) in each dimension of the tensor
                    List<IntVar> labels = new ArrayList<>();
                    for (int h = 0; h < amountOfMatchDays; h++) {
                        labels.add(matchdays[h][i][j]);
                    }

                    IntVar[] intVarArr = convertVarListToArray(labels);

                    //if the elements are equal (eg (0,0),(1,1) sum is zero because we dont want to play ourselves
                    model.sum(intVarArr, "=", 1).post();
                }

            }
        }
    }


    /**Constraint seeds**/

    /**
     * Puts constraints into the model to make sure every team does not play itself
     *  @param amountOfMatchDays
     * @param model
     * @param matchdays
     * @param amountOfTeams
     */
    private static void addNeverPlayYourselfConst(int amountOfMatchDays, Model model, IntVar[][][] matchdays, int amountOfTeams) {
        for (int h = 0; h < amountOfMatchDays; h++) {
            for (int i = 0; i < amountOfTeams; i++) {
                for (int j = 0; j < amountOfTeams; j++) {
                    //this wil make sure the trace of every matchday 2D tensor is 0
                    if (i == j) {
                        model.arithm(matchdays[h][i][j], "=", 0).post();
                    }
                }
            }
        }
    }

    /**
     * Puts the constraint that in each dimension of the tensor, the sum of row i + col i <= 1
     *  @param amountOfMatchDays
     * @param model
     * @param matchdays
     * @param amountOfTeams
     */
    private static void playMaxOneGamePerMatchday(int amountOfMatchDays, Model model, IntVar[][][] matchdays, int amountOfTeams) {

        for (int day = 0; day < amountOfMatchDays; day++) {
            for (int teamIndex = 0; teamIndex < amountOfTeams; teamIndex++) {
                //grab the  row
                List<IntVar> home = Arrays.asList(matchdays[day][teamIndex]);
                //grab the corresponding column
                List<IntVar> away = new ArrayList<>();
                for (int i = 0; i < amountOfTeams; i++) {
                    away.add(matchdays[day][i][teamIndex]);
                }
                //combine them
                List<IntVar> combined = Stream.concat(home.stream(), away.stream())
                        .collect(Collectors.toList());
                //initialize the new array
                IntVar[] intVarArr = convertVarListToArray(combined);
                //either you play 1 game, or you play no game(0)
                model.sum(intVarArr, "<=", 1).post();

            }
        }
    }

    private static void halfWayPointConstraint(int amountOfMatchDays, IntVar[][][] matchdays, Model model, int amountOfTeams) {


        int amountOfMatchdaysInFirstCycle = amountOfMatchDays / 2;
        for (int x = 0; x < amountOfTeams; x++) {
            for (int y = 0; y < amountOfTeams; y++) {
                if (x != y) {
                    ArrayList<IntVar> list = new ArrayList<IntVar>();
                    for (int i = 0; i < amountOfMatchdaysInFirstCycle; i++) {
                        list.add(matchdays[i][x][y]);
                        list.add(matchdays[i][y][x]);
                    }
                    IntVar[] intvars = convertVarListToArray(list);

                    model.sum(intvars, "=", 1).post();

                }
            }
        }
    }

//    private static void homeAndAwayPattern(int amountOfMatchDays,IntVar[][][] matchdays,Model model){
//        int halfwaypoint = (amountOfMatchDays) / 2;
//        for(int teamindex = 0; teamindex<amountOfTeams; teamindex++){
//            for(int day=1;day<=halfwaypoint ;day++){
//                List<IntVar> list = new ArrayList<>(Arrays.asList(matchdays[day][teamindex]));
//                list.addAll(Arrays.asList(matchdays[day-1][teamindex]));
//                model.sum(convertVarListToArray(list),"<=",1).post();
//            }
//        }
//
//
//    }


//    private static void homeAndAwayPattern(int amountOfMatchDays, IntVar[][][] matchdays, Model model) {
//        //we split this in 2 different constraints who partially implicate eachother, first of all: you can't play 2 games in a row at home
//
//            for (int teamIndex = 0; teamIndex < amountOfTeams; teamIndex++) {
//                for (int day = 1; day < amountOfMatchDays; day++) {
//                    List<IntVar> intVarList = new ArrayList<IntVar>(Arrays.asList(matchdays[day][teamIndex]));
//                    intVarList.addAll(Arrays.asList(matchdays[day - 1][teamIndex]));
//                    IntVar[] intvars = convertVarListToArray(intVarList);
//                    model.sum(intvars, "<", 2).post();
//                }
//            }

        //now we do the same for columns, so we don't want 2 away games in a row

//        for(int teamindex = 0; teamindex<amountOfTeams; teamindex++){
//            for(int day = 1; day<amountOfMatchDays;day++){
//                List<IntVar> intVarList = new ArrayList<IntVar>(Arrays.asList(matchdays[day][teamindex]));
//                for(int j = 0; j<amountOfTeams;j++){
//                    intVarList.add(matchdays[day][j][teamindex]);
//                    intVarList.add(matchdays[day-1][j][teamindex]);
//                }
//
//                IntVar[] intvars = convertVarListToArray(intVarList);
//                model.sum(intvars, "<", 2).post();
//
//            }
//
//        }




//    }




    /**Util methods**/


    /**
     * Seeds the roundRobin tensor with an upper and lowerbound (0-1) booleanwise
     * provide eacht IntVar with unique identifier: e.g the value of 0,0,0 means whether on matchday 0 team 0 played team 0
     *  @param amountOfMatchDays the depth dimension
     * @param model             the model that has the tensor injected
     * @param matchdays         the tensor to seed
     * @param amountOfTeams
     */
    private static void seedRobinTensor(int amountOfMatchDays, Model model, IntVar[][][] matchdays, int amountOfTeams) {
        for (int h = 0; h < amountOfMatchDays; h++) {
            for (int i = 0; i < amountOfTeams; i++) {
                for (int j = 0; j < amountOfTeams; j++) {
                    //every element in the  represents a boolean, 0 and 1, we declare every element in the matrix with a unique combination
                    matchdays[h][i][j] = model.intVar(h + "," + i + "," + j, 0, 1);
                }
            }
        }
    }

    private static void prettyPrintSolution(IntVar[][][] matchdays, int amountOfMatchDays, int amountOfTeams) {
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
    private static int calculateMatchDays(int amountOfTeams) {
        if (amountOfTeams % 2 == 0)
            return (amountOfTeams - 1) * 2;
        else return amountOfTeams * 2;
    }

    /**
     * Converts a list of IntVar objects to an array of IntVars
     */
    private static IntVar[] convertVarListToArray(List<IntVar> intVarList) {
        IntVar[] intvars = new IntVar[intVarList.size()];
        intvars = intVarList.toArray(intvars);
        return intvars;
    }

}
