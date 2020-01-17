package util;

import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVRecord;

import java.io.FileReader;
import java.io.IOException;
import java.util.List;

import static util.ConstraintUtils.calculateMatchDays;

public class ValidateUtils {
    public static int[][][] readSolution(String filename) throws IOException {
        //Build reader instance
        CSVParser reader = new CSVParser(new FileReader(filename), CSVFormat.DEFAULT, '"', 1);

        //Read all rows at once, header gets dropped automatically and drop the teamline
        List<CSVRecord> allRows = reader.getRecords();
        allRows.remove(0);
        allRows.remove(0);

        int amtTeams = allRows.size();
        int amtMatchDays = calculateMatchDays(amtTeams);
        int[][][] matchtensor = new int[amtMatchDays][amtTeams][amtTeams];

        for(int d=0;d<amtMatchDays;d++){
            int [][] matchday= new int[amtTeams][amtTeams];
            for(int t=0;t<amtTeams;t++){
                for(int u=0;u<amtTeams;u++){
                    matchday[t][u] = Integer.parseInt(allRows.get(t).get((d*amtTeams+1)+u));
                }
            }
            matchtensor[d] = matchday;
        }
        return matchtensor;
    }


}
