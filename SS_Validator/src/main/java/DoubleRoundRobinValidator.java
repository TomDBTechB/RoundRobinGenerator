import au.com.bytecode.opencsv.CSVReader;
import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVPrinter;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Objects;
import java.util.stream.IntStream;


public class DoubleRoundRobinValidator {


    public static void main(String[] args) throws Exception {

//        String dir = "C:\\KUL\\Masterproef\\Sport-Scheduling-using-Tensor\\choco\\src\\main\\java\\sol";
        String dir = args[0];
        String precOutputDir = args[1];
        File directory = new File(dir);
        if(directory.isDirectory() && directory.listFiles()!=null){
            int csvs = Objects.requireNonNull(Arrays.stream(Objects.requireNonNull(directory.listFiles())).filter(d->d.getAbsolutePath().contains(".csv")).toArray()).length;
            String fileName =precOutputDir+System.getProperty("file.separator")+"T_"+csvs +"Prec.csv";
            try(
                    BufferedWriter writer = Files.newBufferedWriter(Paths.get(fileName));
                    CSVPrinter printer = new CSVPrinter(writer, CSVFormat.DEFAULT)
            ) {
                ArrayList<String> header = new ArrayList<>();
                header.add("file");
                header.add("NeverPlayYS_Cst");
                header.add("NeverPlayYS_Viol");
                header.add("OneGamePerRound_Cst");
                header.add("OneGamePerRound_Viol");
                header.add("Halfway_Cst");
                header.add("Halfway_Viol");
                header.add("PlayEachotherTw_Cst");
                header.add("PlayEachotherTw_Viol");
                printer.printRecord(header);





            for (Object filed : Arrays.stream(Objects.requireNonNull(directory.listFiles())).filter(d->d.getAbsolutePath().contains(".csv")).toArray()) {
                File file = (File) filed;
                ArrayList<String> csvFileLine = new ArrayList<>();
                int[][][] solution = readSolution(file.getAbsolutePath());
                csvFileLine.add(file.getName());


                int[] neverplayyourself = validateNeverPlayYS(solution);
                System.out.println("Never play yourself ==> Amt of const: " + neverplayyourself[0] + " Amt of Violations: " + neverplayyourself[1]);
                csvFileLine.add(String.valueOf(neverplayyourself[0]));
                csvFileLine.add(String.valueOf(neverplayyourself[1]));


                int[] onlyOnePerDay = validatePlayMaxOneGamePerMatchday(solution);
//                System.out.println("Only one game per round => Amt of Const: " + onlyOnePerDay[0] + " Amt of Violations: " + onlyOnePerDay[1]);
                csvFileLine.add(String.valueOf(onlyOnePerDay[0]));
                csvFileLine.add(String.valueOf(onlyOnePerDay[1]));
                int [] halfway = playEachotherHalfway(solution);
                csvFileLine.add(String.valueOf(halfway[0]));
                csvFileLine.add(String.valueOf(halfway[1]));
//                System.out.println("Play eachother halfway once => Amt of const: " + halfway[0] + " Amt of Violations: " + halfway[1]);
                int [] playeachotherTwice = validatePlayEachotherTwice(solution);
//                System.out.println("Play eachother twice => Amt of Const: " + playeachotherTwice[0] + " Amt of Violations: " + playeachotherTwice[1]);
                csvFileLine.add(String.valueOf(playeachotherTwice[0]));
                csvFileLine.add(String.valueOf(playeachotherTwice[1]));

                printer.printRecord(csvFileLine);
                printer.flush();

            }



            }

        }



    }

    private static int[] playEachotherHalfway(int[][][] solution) {
        int [] values = new int[2];
        int halfwaypoint = solution[0].length/2;

        for(int t=0;t<solution[0].length;t++){
            for(int u=0; u<solution[0].length;u++){
                if(t!=u){
                    values[0]++;
                    int matchesPlayed = 0;
                    for(int d=0; d< halfwaypoint; d++){
                        matchesPlayed+= solution[d][t][u] + solution[d][u][t];
                    }
                    if(matchesPlayed!=1) values[1]++;
                }

            }
        }

        return values;


    }

    private static int[] validatePlayEachotherTwice(int[][][] solution) {
        int[] values = new int[2];
        for(int t=0;t<solution[0].length;t++){
            for(int u=0; u<solution[0].length;u++){
                if(t!=u){
                    values[0]++;
                    int matchesPlayed = 0;
                    for(int d=0; d< solution.length; d++){
                        matchesPlayed+= solution[d][t][u] + solution[d][u][t];
                    }
                    if(matchesPlayed!=2) values[1]++;
                }

            }
        }

        return values;
    }

    private static int[] validateNeverPlayYS(int[][][] solution) {
        int[] values = new int[2];
        for (int[][] aSolution : solution) {
            for (int i = 0; i < aSolution.length; i++) {
                values[0]++;
                if (aSolution[i][i] != 0) {
                    values[1]++;

                }
            }
        }


        return values;

    }

    private static int[] validatePlayMaxOneGamePerMatchday(int[][][] solution) {
        int[] values = new int[2];
        for (int h = 0; h < solution.length; h++) {
            int[][] matchday = solution[h];
            for (int t = 0; t < matchday.length; t++) {
                int sumhome = IntStream.of(matchday[t]).sum();
                int awayRow = 0;
                for (int u = 0; u < matchday[t].length; u++) {
                    awayRow += matchday[u][t];
                }
                values[0]++;
                if (sumhome + awayRow > 1) {
                    values[1]++;
                }
            }
        }
        return values;
    }

    private static int[][][] readSolution(String filename) throws IOException {
        //Build reader instance
        CSVReader reader = new CSVReader(new FileReader(filename), ',', '"', 1);

        //Read all rows at once, header gets dropped automatically and drop the teamline
        List<String[]> allRows = reader.readAll();
        allRows.remove(0);

        int amtTeams = allRows.size();
        int amtMatchDays = calculateMatchDays(amtTeams);
        int[][][] matchtensor = new int[amtMatchDays][amtTeams][amtTeams];

        for (int d = 0; d < amtMatchDays; d++) {
            int[][] matchday = new int[amtTeams][amtTeams];
            for (int i = 0; i < amtTeams; i++) {
                for (int j = 0; j < amtTeams; j++) {
                    matchday[i][j] = Integer.parseInt(allRows.get(i)[(d * amtTeams + 1) + j]);
                }
            }

            matchtensor[d] = matchday;
        }
        return matchtensor;
    }

    private static int calculateMatchDays(int amountOfTeams) {
        if (amountOfTeams % 2 == 0)
            return (amountOfTeams - 1) * 2;
        else return amountOfTeams * 2;
    }
}

