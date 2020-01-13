package util;

import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVPrinter;
import org.chocosolver.solver.variables.IntVar;

import java.io.BufferedWriter;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;

public class CsvWriter {
    private static final String NEW_LINE_SEPARATOR = "\n";


    public static void createSample(IntVar[][][] matchdays, int amountOfMatchDays, int amountOfTeams, int counter, String sampleDirectory){
        String fileName = sampleDirectory+System.getProperty("file.separator")+amountOfTeams+"T_"+counter+".csv";

        try {
            boolean thefile = new File(fileName).createNewFile();
        } catch (IOException e) {
            System.out.println(e.toString());        }

        try(
                BufferedWriter writer = Files.newBufferedWriter(Paths.get(fileName));
                CSVPrinter printer = new CSVPrinter(writer, CSVFormat.DEFAULT)
        ) {

            ArrayList<String> headerList = new ArrayList<String>();
            ArrayList<String> headerList2 = new ArrayList<String>();

            headerList.add("");
            headerList2.add("");

            for (int j = 0; j<amountOfMatchDays;j++){
                for(int i=0;i<amountOfTeams;i++){
                    headerList.add("M"+j);
                    int index = i+1;
                    headerList2.add("T"+index);

                }
            }

            printer.printRecord(headerList);
            printer.printRecord(headerList2);

            for(int teamindex = 0;teamindex<amountOfTeams;teamindex++){
                ArrayList<String> teamlist = new ArrayList<String>();
                int index = teamindex+1;
                teamlist.add("T"+index);
                for(int matchday=0;matchday<amountOfMatchDays;matchday++){
                    for(int hometeam =0;hometeam<amountOfTeams;hometeam++){
                        teamlist.add(String.valueOf(matchdays[matchday][teamindex][hometeam].getValue()));
                    }
                }
                printer.printRecord(teamlist);
                printer.flush();


            }

        } catch (IOException e) {
            System.out.println(e.toString());
            System.err.println("Fatal error when opening/writing to "+fileName);
        }

    }

}
