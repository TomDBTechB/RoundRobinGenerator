package generator;

public class UnusedConstraints {


/*
            //constraint U02
            private static void seedNeverPlayYS (Model m, IntVar[][][][]matchdays,int amountOfCycles,
            int amountOfMatchdays, int amountOFTeams){
            for (int c = 0; c < amountOfCycles; c++) {
                for (int day = 0; day < amountOfMatchdays; day++) {
                    for (int teams = 0; teams < amountOFTeams; teams++) {
                        m.arithm(matchdays[c][day][teams][teams], "=", 0).post();
                    }
                }
            }
        }

            //constraint P04
            private static void seedTeamNotPlayAtHomeInRound (Model m, IntVar[][][]matchdays,int day, int team){
            m.sum(matchdays[day][team], "=", 0).post();
        }
            //constraint P05
            private static void seedTeamNotPlayAwayInRound (Model m, IntVar[][][]matchdays,int day, int team){
            List<IntVar> awayfields = new ArrayList<>();
            for (int t = 0; t < matchdays[day][team].length; t++) {
                awayfields.add(matchdays[day][t][team]);
            }
            m.sum(ConstraintUtils.convertVarListToArray(awayfields), "=", 0).post();
        }
            //constraint P06
            private static void seedTeamNotPlayAtAllAtRound (Model m, IntVar[][][]matchdays,int day, int team){
            List<IntVar> awayfields = new ArrayList<>();
            for (int t = 0; t < matchdays[day][team].length; t++) {
                awayfields.add(matchdays[day][t][team]);
            }
            m.sum(ConstraintUtils.convertVarListToArray(awayfields), "=", 0).post();
            m.sum(matchdays[day][team], "=", 0).post();
        }

            //constraint G10
            private static void seedGameBetweenTeamsInRound (Model m, IntVar[][][]matchdays,int day, int home, int away)
            {
                m.arithm(matchdays[day][home][away], "=", 1).post();
            }

            //constraint G11
            private static void seedNoGameBetweenTeamsInRound (Model m, IntVar[][][]matchdays,int day, int home,
            int away){
            m.arithm(matchdays[day][home][away], "=", 0).post();
        }

            //constraint G24
            private static void seedNoGameBeforeRound (Model m, IntVar[][][]matchdays,int home, int away, int round){
            List<IntVar> fields = new ArrayList<>();
            for (int d = 0; d < round - 1; d++) {
                fields.add(matchdays[d][home][away]);
            }
            m.sum(ConstraintUtils.convertVarListToArray(fields), "=", 0).post();
        }
            //Constraint G25
            private static void seedNoGameAfterRound (Model m, IntVar[][][]matchdays,int home, int away, int round){
            List<IntVar> fields = new ArrayList<>();
            for (int d = round; d < matchdays.length; d++) {
                fields.add(matchdays[d][home][away]);
            }
            m.sum(ConstraintUtils.convertVarListToArray(fields), "=", 0).post();
        }
            //Constraint G34
            private static void seedGameInSubset (Model m, IntVar[][][]matchdays,int home, int away, int[] subset){
            List<IntVar> fields = new ArrayList<>();
            for (int i : subset) {
                fields.add(matchdays[i][home][away]);
            }
            m.sum(ConstraintUtils.convertVarListToArray(fields), "=", 1).post();
        }
            //constraint 5+6
    private static void seedTotalAmountOfGamesPerTeam(Model m, IntVar[][][][] matchdays, int amountOfMatchdays, int amountOfTeams)
        {
            for (int c = 0; c < matchdays.length; c++) {
                for (int team = 0; team < amountOfTeams; team++) {
                    List<IntVar> teamFields = new ArrayList<>();
                    for (int day = 0; day < amountOfMatchdays; day++) {
                        teamFields.addAll(Arrays.asList(matchdays[day][team]));
                        for (int kolom = 0; kolom < amountOfTeams; kolom++)
                            teamFields.add(matchdays[day][kolom][team]);
                    }
                    m.sum(ConstraintUtils.convertVarListToArray(teamFields), "<=", UPPER_BOUND_TOTAL_GAMES).post();
                    m.sum(ConstraintUtils.convertVarListToArray(teamFields), ">=", LOWER_BOUND_TOTAL_GAMES).post();

                }
            }
        }


        */

}
