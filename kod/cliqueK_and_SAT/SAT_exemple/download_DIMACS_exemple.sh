#!/bin/bash
# download_dimacs.sh

echo "Creating DIMACS folder structure..."
mkdir -p DIMACS/{AIM,DUBOIS,PHOLE,GCP,PARITY,JNH}

echo "Getting benchmark sets..."
cd DIMACS

# Core benchmark sets
wget https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/DIMACS/AIM/aim.tar.gz
wget https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/DIMACS/DUBOIS/dubois.tar.gz
wget https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/DIMACS/PHOLE/pigeon-hole.tar.gz
wget https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/DIMACS/GCP/gcp-large.tar.gz
wget https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/DIMACS/PARITY/parity.tar.gz
wget https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/DIMACS/JNH/jnh.tar.gz

echo "unziping..."
tar -xzf aim.tar.gz -C AIM/
tar -xzf dubois.tar.gz -C DUBOIS/
tar -xzf pigeon-hole.tar.gz -C PHOLE/
tar -xzf gcp-large.tar.gz -C GCP/
tar -xzf parity.tar.gz -C PARITY/
tar -xzf jnh.tar.gz -C JNH/

echo "Cleaning tar files..."
rm *.tar.gz

cd ..
