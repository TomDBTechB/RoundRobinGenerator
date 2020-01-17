package generator;

import org.apache.commons.lang3.ArrayUtils;
import util.ValidateUtils;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import static util.ValidateUtils.readSolution;

public class SportScheduleValidator {

    //Constraint 1 + 2
    private static final int LOWER_BOUND_HOMEGAMES_PER_TEAM = 5;
    private static final int UPPER_BOUND_HOMEGAMES_PER_TEAM = 5;
    private static final int UPPER_BOUND_AWAYGAMES_PER_TEAM = 5;
    private static final int LOWER_BOUND_AWAYGAMES_PER_TEAM = 5;
    private static final int UPPER_BOUND_FIXTURE_HAPPENING = 1;
    private static final int LOWER_BOUND_FIXTURE_HAPPENING = 0;
    private static final int LOWER_BOUND_HOME_GAME_PER_DAY = 0;
    private static final int UPPER_BOUND_HOME_GAME_PER_DAY = 1;
    private static final int LOWER_BOUND_AWAY_GAME_PER_DAY = 0;
    private static final int UPPER_BOUND_AWAY_GAME_PER_DAY = 1;
    private static final int LOWER_BOUND_GAMES_PER_DAY = 3;
    private static final int UPPER_BOUND_GAMES_PER_DAY = 3;


    public static void main(String[] args) {
        String sampleDirectory = args[0];
        //String sampleDirectory = "/home/tom/Documents/Masterproef/Codebase/Sport-Scheduling-using-Tensor/CountOR-code/countSport/data/6_100/tmp";


        try(Stream<Path> walk = Files.walk(Paths.get(sampleDirectory))){
            List<String> filenames= walk.filter(Files::isRegularFile).map(Path::toString).collect(Collectors.toList());

            double precisionFolder = validateSamples(filenames);
            System.out.println(precisionFolder);




        } catch (IOException e){
            System.err.println("Something went wrong while reading the files");
            e.printStackTrace();
        }


    }

    private static double validateSamples(List<String> filenames) throws IOException {
        double validsamples = 0;
        for (String filename : filenames) {
            int [][][] matchtensor = ValidateUtils.readSolution(filename);


            boolean b = validateAmountAwayGamesPerTeam(matchtensor);
            boolean b1 = validateAmountHomeGamesPerTeam(matchtensor);
            boolean b2 = validateAmoutOfFixtureOccurence(matchtensor);
            boolean b3 = validateAmountOfAwaygamesPlayedPerDayPerTeam(matchtensor);
            boolean b4 = validateAmountOfHomegamesPlayedPerDayPerTeam(matchtensor);
            boolean b5 = validateGamesPerDay(matchtensor);
            if(b && b1
                    && b2 && b3
                    && b4 && b5){
                validsamples++;
            }


        }
        return validsamples/(double)filenames.size();
    }




    private static boolean validateAmountHomeGamesPerTeam(int[][][] matchtensor){
        int amtOfDays = matchtensor.length;
        int amtOfTeams = matchtensor[0].length;

        for(int teams=0;teams<amtOfTeams;teams++){
            int[] matchindices = new int[0];
            for (int[][] ints : matchtensor) {
                matchindices = ArrayUtils.addAll(matchindices, ints[teams]);
            }
            int totalHomeGames = Arrays.stream(matchindices).sum();
            if(!(LOWER_BOUND_HOMEGAMES_PER_TEAM <= totalHomeGames && totalHomeGames<=UPPER_BOUND_HOMEGAMES_PER_TEAM)){
                return false;
            }
        }

        return true;
    }

    private static boolean validateAmountAwayGamesPerTeam(int[][][] matchtensor){
        int amtOfDays = matchtensor.length;
        int amtOfTeams = matchtensor[0].length;


        for(int teams=0;teams<amtOfTeams;teams++) {
            int[] matchindices = new int[0];
            for (int[][] ints : matchtensor) {
                for (int col = 0; col < amtOfTeams; col++) {
                    matchindices = ArrayUtils.add(matchindices, ints[col][teams]);
                }
            }
            int totalAwayGames = Arrays.stream(matchindices).sum();
            if(!(LOWER_BOUND_AWAYGAMES_PER_TEAM <= totalAwayGames && totalAwayGames<=UPPER_BOUND_AWAYGAMES_PER_TEAM)){
                return false;
            }

        }
        return true;
    }

    private static boolean validateAmoutOfFixtureOccurence(int[][][] matchtensor){
        int amtOfTeams = matchtensor[0].length;

        for(int team=0;team<amtOfTeams;team++){
            for(int col=0;col<amtOfTeams;col++){
                int[] fixture = new int[0];
                for (int[][] ints : matchtensor) {
                    fixture = ArrayUtils.add(fixture, ints[col][team]);
                }
                int fixtureamt = Arrays.stream(fixture).sum();
                if(!( LOWER_BOUND_FIXTURE_HAPPENING<= fixtureamt && fixtureamt<=UPPER_BOUND_FIXTURE_HAPPENING)){
                    return false;
                }
            }
        }
        return true;
    }

    private static boolean validateAmountOfHomegamesPlayedPerDayPerTeam(int[][][] matchtensor){
        int amtMatchDays = matchtensor.length;
        int amtTeams = matchtensor[0].length;
        for(int day=0; day<amtMatchDays;day++){
            for(int team=0;team<amtTeams;team++){
                int total= Arrays.stream(matchtensor[day][team]).sum();
                if(!(LOWER_BOUND_HOME_GAME_PER_DAY <= total && total<=UPPER_BOUND_HOME_GAME_PER_DAY)){
                    return false;
                }
            }
        }
        return true;
    }

    private static boolean validateAmountOfAwaygamesPlayedPerDayPerTeam(int[][][] matchtensor){
        int amtMatchDays = matchtensor.length;
        int amtTeams = matchtensor[0].length;
        for (int[][] ints : matchtensor) {
            for (int team = 0; team < amtTeams; team++) {
                int[] away = new int[0];
                for (int col = 0; col < amtTeams; col++) {
                    away = ArrayUtils.add(away, ints[col][team]);
                }
                int total = Arrays.stream(away).sum();
                if (!(LOWER_BOUND_AWAY_GAME_PER_DAY <= total && total <= UPPER_BOUND_AWAY_GAME_PER_DAY)) {
                    return false;
                }

            }
        }
        return true;
    }

    private static boolean validateGamesPerDay(int[][][] matchtensor){
        int amtMatchdays = matchtensor.length;
        int amtTeams = matchtensor[0].length;

        for (int[][] ints : matchtensor) {
            int[] fixturefields = new int[0];
            for (int team = 0; team < amtTeams; team++) {
                fixturefields = ArrayUtils.addAll(fixturefields, ints[team]);
            }
            int total = Arrays.stream(fixturefields).sum();

            if (!(LOWER_BOUND_GAMES_PER_DAY <= total && total <= UPPER_BOUND_GAMES_PER_DAY)) {
                return false;
            }

        }

        return true;



    }


}
