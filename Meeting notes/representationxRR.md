# Representation of Sports data in a simple xRR format for n teams
- Important to note, we won't yet make a format based on timeslots, just the playweek schedule (so the planning of what game played in what week)
- We assume 5 teams who play eachoter 2 times, so each team plays 8 games, thus there is a minimum of n-1 matchdays for a cycle, a maximum of n matchdays for a cycle 
  - n teams --> (n-1)*x games during the full xRR tournament

- The sum of all dimensions should look like this (SUM(X[g])) with g the number of games
0	1	1	1	1
1	0	1	1	1
1	1	0	1	1
1	1	1	0	1
1	1	1	1	0

  - Following rather trivial constraints follow
    - Tr(X) = 0 
    - Dim(X) = n 

  - A team only plays each other team twice (home and away)
  - A team can't play itself

- Lets take a look at a possible decomposition for the 5 matchdays

0	1	0	0	1
0	0	1	1	0
1	0	0	0	1
0	0	1	0	0
0	0	0	1	0


X[g(1)]
0	1	0	0	0
0	0	0	0	0
0	0	0	0	0
0	0	1	0	0
0	0	0	0	0
- A - B
- D - C
- E: bye


X[g(2)]
0	0	0	0	0
0	0	0	1	0
0	0	0	0	1
0	0	0	0	0
0	0	0	0	0
- B - D
- C - E
- A: bye

X[g(3)]
0	0	0	0	0
0	0	0	0	0
0	0	0	0	0
1	0	0	0	0
0	1	0	0	0
- D vs A
- E vs B
- C: bye


0	0	0	0	1
0	0	1	0	0
0	0	0	0	0
0	0	0	0	0
0	0	0	0	0
- A vs E
- B vs C
- D is free

0	0	0	0	0
0	0	0	0	0
1	0	0	0	0
0	0	0	0	0
0	0	0	1	0
- E vs D
- C vs A
- B is free

This is the first cycle of our round robin tournament, and a couple of constraints  pop up very clearly

- T(X[g(1|2|3)]) = 0 (you still cant play yourself)
- T(X[g(1|2|3)]) only contain n/2 1 values for each dimension (dont really know how to put this )
- Sum T(X[g(123)]) contains on n-1 1's on row x and col x combined voor x going from 1 to n-1
  - Each team has played each team exactly once now
- We want to minimize the amount of consecutive home/away games, so if in dim 1
  - SUM(row 1) = 1 and SUM(col 1) = 0, than you should have in dim 2
    - SUM (row 1) = 0 and SUM(col 1) = 1 OR SUM(row 1) = 0 and SUM(row 1 = 0)
    - if you play at home in week 1, you play away week 2, or you have a bye
- BYE CONSTRAINT?

- An interseting fact is if we want a mirrored round robin competition, so in the 2nd cycle we want for example first matchday  B vs A and C vs D (this only works for even number of teams)
  - Just transpose the first 3 dimensions to get what we want
- these constraints are offcourse non binding if we consider edge cases, but those are not important right now

# Problem statement + Research approach: presentation 25/10

- Context
  - many problems in real world require constraints
  - scheduling is a very laboursome task, e.g the major league baseball
    - 2 leagues
    - 3 division in a league
    - 162 games played per team per regular seaons (from march-october )
  - In what ways could this scheduling task be automated to lower the amount of labor?

- Aim
  - How could we use/adapt count-or to learn and acquire 

- Approach
  - Literature study on 3 areas
    - What are sport tournaments, what is the used terminology within here?
    - What are frequently used sport constraints and how could we learn this
    - How can we use tensor manipulation 

  - Research questions?
    - How are we going to represent the sportschedules in tensor data?
      - This is almost done, only need to discuss how to put a fourth dimension in the tensor, it's not yet clear how to represent this for me
    - What could we learn if we use CountOR for this representation as is?
      - Don't expect a lot about this one, but it could be an option to take a quick look at it
    - Can we manage to learn sport constraints from our tensor data?
      - approach: use a constraint solver to generate tensors that follow the constraints above
      - convert solutions to the 4D tensors
      - Run the count-or adaptation/figure something out of our own
      - see what constraints get learned
        - Adaptation for multiple schedules is just an adaptation of the ranges of multiple constraints

      - No edge cases come in to play here

- Use case
  - Schedule the belgium football competition? 9 available schedules
    - 16 teams --> 30 games in regular competition
    - playoffs in divisions of 6 teams --> 10 games in playoffs
    - lots of edge cases, considering to directly contact domain experts
      - e.g Champions league, europa league, interland breaks, etc...
