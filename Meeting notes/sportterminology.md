# Notes meeting 2
#### Step 1: Defining different possible schedule tournaments and the terminology

1. Round robin tournaments
	- 1RR: Every participant meets eachother only once: e.g group phase world cup.
		- Look for a way to represent a tournament tree in tensors? --> not really pure round robin, but could be considered as a multiple stage round robin
	- 2RR: Every participant meets eachother twice:     e.g regular competition jupiler pro league --> Double RR = most common
	- 4RR: Every participant meets eachother 4 times:   e.g 1B belgian footbal, scottish first class competition 

	- RR Doublie split --> split into different divisions and have the best participants play off in a new Round robin knockout phase
	- RR triple split --> Split into 3 divisions --> problem
2. Round
	- Every tournament consists of multiple rounds (matchdays) 
	- Important constraint here: every participant only competes once in a matchday
	- amount om rounds --> if number of participents is even --> min amount of rounds = n-1, if odd = n
	- compact is the lower bound, if more, the tournament is relaxed
	- A round consists of multiple fixtures, and a fixture consists of 2 participants playing eachother

3. HAP patterns
	- When we look at football, we always speak of a home and an away team --> HAP (home and away pattern)
	- If a team is free for a round and doesn't have to play , it has a bye
	- break == consecutive series of home/away games
	- Equitable HAP if all teams have the same break length

4. timetables
	- The stuff we are going to translate to tensors (the assignment of different fixtures to available timeslots)

#### Step 2: What is the next step to research?

*A first approach:* imagine a simple tournament 16 teams play in a single tournament max 2 games per day (Slot 1/slot 2) and after every round a rest day
Just convert it to tensors and see what happens, a problem here could be that we need to decide a new form of representation, because we need a way to combine home-away for teams
If it's bad, try to see what tweaks are necessary and see if the tweaks are a way to generify


*Possible research approaches*

1. What are the different scheduling manners in sport
2. What constraints live within the sportsworld --> pull it open and touch 3/4 federations?
3. Is it possible to generate simple RR schemes using CountOR without using any edits?
4. Use case: scheduling the belgium regular competition/playoffs (if they ever answer)
5. Use case: scheduling for the FTTL (Flemish Table Tennis League)




- Data --> Tensor
- Constraints --> Tensor language (how many constraints can be relearned)
- Minizinc / Gurobi


