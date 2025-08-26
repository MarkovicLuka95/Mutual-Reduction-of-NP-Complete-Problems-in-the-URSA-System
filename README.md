# Mutual-Reduction-of-NP-Complete-Problems-in-the-URSA-System
Implementation and analysis of reductions among NP-complete problems within the URSA system.

For using URSA, follow the instructions: https://github.com/janicicpredrag/URSA

to install minisat:
sudo apt update
sudo apt install minisat

to run py scripts:
python3 ursa_starter.py SATexemple/DIMACS/ --solver-template sat_template.urs --reduction-template sat_to_cliqueK_template.urs --timeout 150
