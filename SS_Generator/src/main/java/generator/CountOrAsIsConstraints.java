package generator;

import org.chocosolver.solver.Model;
import org.chocosolver.solver.variables.IntVar;
import util.ConstraintUtils;
import util.CsvWriter;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class CountOrAsIsConstraints {

    //Constraint 1 + 2
    private static final int LOWER_BOUND_HOMEGAMES_PER_TEAM = 5;
    private static final int UPPER_BOUND_HOMEGAMES_PER_TEAM = 5;
    private static final int UPPER_BOUND_AWAY_GAMES = 5;
    private static final int LOWER_BOUND_AWAYGAMES = 5;

    //Constraint 12
    private static final int UPPER_BOUND_TOTAL_GAMES_PER_DAY = 3;
    private static final int LOWER_BOUND_TOTAL_GAMES_PER_DAY = 3;

    //constraint 5+6
    private static final int LOWER_BOUND_TOTAL_GAMES = 10;
    private static final int UPPER_BOUND_TOTAL_GAMES = 10;


    //constraint 7 + 8
    //these remain the same for odd and even teams
    private static final int LOWER_BOUND_HOME_GAME_PER_DAY = 0;
    private static final int UPPER_BOUND_HOME_GAME_PER_DAY = 1;
    private static final int LOWER_BOUND_AWAY_GAME_PER_DAY = 0;
    private static final int UPPER_BOUND_AWAY_GAME_PER_DAY = 1;

    //constraint 9: the fixture gets played or it doesn't(happens when home-team = away-team)
    private static final int UPPER_BOUND_FIXTURE_HAPPENING = 1;
    private static final int LOWER_BOUND_FIXTURE_HAPPENING = 0;


    public static void main(String[] args) {
        int amountOfTeams = Integer.parseInt(args[0]);
        int amountOfSamples = Integer.parseInt(args[1]);
        String sampleDirectory = args[2];


        int amountOfMatchDays = ConstraintUtils.calculateMatchDays(amountOfTeams);
        Model model = new Model("RoundRobinGen");

        IntVar [][][] matchDays = ConstraintUtils.seedRobinTensor(amountOfMatchDays,model,amountOfTeams);

        seedTotalAmountOfHomeGamesPerTeam(model,matchDays,amountOfMatchDays,amountOfTeams);
        seedTotalAmountOfAwayGamesPerTeam(model,matchDays,amountOfMatchDays,amountOfTeams);
        //this one is redundant (since the sum of your home games + the sum of away games = total amount of games)
        seedTotalAmountOfGamesPerTeam(model,matchDays,amountOfMatchDays,amountOfTeams);

        seedTotalAmountOfGamesPerDay(model,matchDays,amountOfMatchDays,amountOfTeams);
        seedAmountOfAwayGamesPlayedPerDayPerTeam(model,matchDays,amountOfMatchDays,amountOfTeams);
        seedAmountOfHomeGamesPlayedPerDayPerTeam(model,matchDays,amountOfMatchDays,amountOfTeams);

        seedAmountOfFixturesOccurence(model,matchDays,amountOfMatchDays,amountOfTeams);


        int counter = 0;
        model.getSolver().limitSolution(amountOfSamples);
        while (model.getSolver().solve()&& counter<amountOfSamples) {
            CsvWriter.createSample(matchDays,amountOfMatchDays,amountOfTeams,counter,sampleDirectory);
            counter++;
        }
    }



    //constraint 1
    private static void seedTotalAmountOfHomeGamesPerTeam(Model m, IntVar[][][] matchDays, int amountOfMatchDays, int amountOfTeams) {
        for (int team = 0; team < amountOfTeams; team++){
            List<IntVar> homeRows = new ArrayList<>();
            for (int day = 0; day < amountOfMatchDays; day++){
                homeRows.addAll(Arrays.asList(matchDays[day][team]));
            }
            m.sum(ConstraintUtils.convertVarListToArray(homeRows),"<=", UPPER_BOUND_HOMEGAMES_PER_TEAM).post();
            m.sum(ConstraintUtils.convertVarListToArray(homeRows),">=", LOWER_BOUND_HOMEGAMES_PER_TEAM).post();
        }
    }

    //constraint 2
    private static void seedTotalAmountOfAwayGamesPerTeam(Model m, IntVar[][][] matchdays, int amountOfMatchdays, int amountOfTeams){
        for(int team =0; team<amountOfTeams; team++){
            List<IntVar> AwayFields = new ArrayList<>();
            for(int day = 0; day < amountOfMatchdays; day++){
                for(int kolom = 0; kolom<amountOfTeams;kolom++)
                    AwayFields.add(matchdays[day][kolom][team]);
            }
            m.sum(ConstraintUtils.convertVarListToArray(AwayFields),"<=", UPPER_BOUND_AWAY_GAMES).post();
            m.sum(ConstraintUtils.convertVarListToArray(AwayFields),">=",LOWER_BOUND_AWAYGAMES).post();
        }
    }

    //constraint 12
    private static void seedTotalAmountOfGamesPerDay(Model m, IntVar[][][] matchdays,int amountOfMatchdays,int amountOfTeams){
        for(int day=0;day<amountOfMatchdays; day++){
            List<IntVar> fixtureFields = new ArrayList<>();
            for(int team = 0;team<amountOfTeams;team++){
                fixtureFields.addAll(Arrays.asList(matchdays[day][team]));
            }

            m.sum(ConstraintUtils.convertVarListToArray(fixtureFields),"<=", UPPER_BOUND_TOTAL_GAMES_PER_DAY).post();
            m.sum(ConstraintUtils.convertVarListToArray(fixtureFields),">=",LOWER_BOUND_TOTAL_GAMES_PER_DAY).post();
        }
    }


    //constraint 5+6
    private static void seedTotalAmountOfGamesPerTeam(Model m, IntVar[][][] matchdays, int amountOfMatchdays, int amountOfTeams){
        for(int team =0;team<amountOfTeams;team++){
            List<IntVar> teamFields = new ArrayList<>();
            for(int day=0; day<amountOfMatchdays;day++){
                teamFields.addAll(Arrays.asList(matchdays[day][team]));
                for(int kolom = 0; kolom<amountOfTeams;kolom++)
                    teamFields.add(matchdays[day][kolom][team]);
            }
            m.sum(ConstraintUtils.convertVarListToArray(teamFields),"<=", UPPER_BOUND_TOTAL_GAMES).post();
            m.sum(ConstraintUtils.convertVarListToArray(teamFields),">=",LOWER_BOUND_TOTAL_GAMES).post();

        }
    }

    //constraint 7
    private static void seedAmountOfAwayGamesPlayedPerDayPerTeam(Model m, IntVar[][][] matchdays, int amountOfMatchDays, int amountOfTeams){
        for(int day=0; day <amountOfMatchDays;day++){
            for(int team=0; team<amountOfTeams; team++){
                List<IntVar> awayColumns = new ArrayList<>();
                for(int kolomindex = 0; kolomindex<amountOfTeams; kolomindex++){
                    awayColumns.add(matchdays[day][kolomindex][team]);
                }
                m.sum(ConstraintUtils.convertVarListToArray(awayColumns),"<=",UPPER_BOUND_AWAY_GAME_PER_DAY).post();
                m.sum(ConstraintUtils.convertVarListToArray(awayColumns),">=",LOWER_BOUND_AWAY_GAME_PER_DAY).post();



            }
        }
    }

    //constraint 8
    private static void seedAmountOfHomeGamesPlayedPerDayPerTeam(Model m, IntVar[][][] matchdays, int amountOfMatchdays, int amountOfTeams){
        for(int day = 0; day <amountOfMatchdays; day++){
            for(int team = 0; team<amountOfTeams; team++){
                IntVar[] homeRows = matchdays[day][team];
                m.sum(homeRows,"<=", UPPER_BOUND_HOME_GAME_PER_DAY).post();
                m.sum(homeRows,">=", LOWER_BOUND_HOME_GAME_PER_DAY).post();
            }
        }
    }

    //constraint 9
    private static void seedAmountOfFixturesOccurence(Model m, IntVar[][][] matchdays, int amountOfMatchdays,int amountOfTeams){
        for(int team=0;team<amountOfTeams; team++){
            for(int column=0;column<amountOfTeams;column++){
                List<IntVar> fixture = new ArrayList<>();
                for(int day=0;day<amountOfMatchdays;day++){
                    fixture.add(matchdays[day][column][team]);
                }
                m.sum(ConstraintUtils.convertVarListToArray(fixture),"<=",UPPER_BOUND_FIXTURE_HAPPENING).post();
                m.sum(ConstraintUtils.convertVarListToArray(fixture),">=",LOWER_BOUND_FIXTURE_HAPPENING).post();
            }
        }
    }











}
