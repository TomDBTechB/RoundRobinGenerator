package generator;

import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVRecord;
import org.apache.commons.lang3.ArrayUtils;

import java.io.FileReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;
import java.util.stream.Stream;

import static util.ConstraintUtils.calculateMatchDays;

public class SportScheduleValidator {

    //Constraint 1 + 2
    private static final int LOWER_BOUND_HOMEGAMES_PER_TEAM = 5;
    private static final int UPPER_BOUND_HOMEGAMES_PER_TEAM = 5;
    private static final int UPPER_BOUND_AWAYGAMES_PER_TEAM = 5;
    private static final int LOWER_BOUND_AWAYGAMES_PER_TEAM = 5;
    private static final int UPPER_BOUND_FIXTURE_HAPPENING = 1;
    private static final int LOWER_BOUND_FIXTURE_HAPPENING = 0;

    public static void main(String[] args) {
        //String sampleDirectory = args[0];
        String sampleDirectory = "/home/tom/Documents/Masterproef/Codebase/Sport-Scheduling-using-Tensor/CountOR-code/countSport/data/6_100/tmp";


        try(Stream<Path> walk = Files.walk(Paths.get(sampleDirectory))){
            List<String> filenames= walk.filter(Files::isRegularFile).map(Path::toString).collect(Collectors.toList());

            double precisionFolder = validateSamples(filenames);


        } catch (IOException e){
            System.err.println("Something went wrong while reading the files");
            e.printStackTrace();
        }


    }

    private static double validateSamples(List<String> filenames) throws IOException {
        for (String filename : filenames) {
            int [][][] matchtensor = readSolution(filename);

        }


        return 0;
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
            if(LOWER_BOUND_HOMEGAMES_PER_TEAM <= totalHomeGames && totalHomeGames<=UPPER_BOUND_HOMEGAMES_PER_TEAM){
                return false;
            }
        }

        return true;
    }

    private static boolean validateAmountAwayGamesPerTeam(int[][][] matchtensor){
        int amtOfDays = matchtensor.length;
        int amtOfTeams = matchtensor[0].length;

        int[] awaygames = new int[0];

        for(int teams=0;teams<amtOfTeams;teams++) {
            int[] matchindices = new int[0];
            for (int[][] ints : matchtensor) {
                for (int col = 0; col < amtOfTeams; col++) {
                    awaygames = ArrayUtils.add(matchindices, ints[col][teams]);
                }
            }
            int totalAwayGames = Arrays.stream(awaygames).sum();
            if(LOWER_BOUND_AWAYGAMES_PER_TEAM <= totalAwayGames && totalAwayGames<=UPPER_BOUND_AWAYGAMES_PER_TEAM){
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
                if( LOWER_BOUND_FIXTURE_HAPPENING<= fixtureamt && fixtureamt<=UPPER_BOUND_FIXTURE_HAPPENING){
                    return false;
                }
            }
        }
        return true;
    }

    private static boolean validateAmountOfHomegamesPlayedPerDayPerTeam(int[][][] matchtensor){
        return false;
    }


    private static int[][][] readSolution(String filename) throws IOException {
        //Build reader instance
        CSVParser reader = new CSVParser(new FileReader(filename), CSVFormat.DEFAULT, '"', 1);

        //Read all rows at once, header gets dropped automatically and drop the teamline
        List<CSVRecord> allRows = reader.getRecords();
        allRows.remove(0);
        allRows.remove(1);

        int amtTeams = allRows.size();
        int amtMatchDays = calculateMatchDays(amtTeams);
        int[][][] matchtensor = new int[amtMatchDays][amtTeams][amtTeams];

        for(int d=0;d<amtMatchDays;d++){
            int [][] matchday= new int[amtTeams][amtTeams];
            for(int t=0;t<amtTeams;t++){
                for(int u=0;u<amtTeams;u++){
                    matchday[t][u] = Integer.parseInt(allRows.get(d).get((d*amtTeams+1)+u));
                }
            }
            matchtensor[d] = matchday;
        }
        return matchtensor;
    }
}
