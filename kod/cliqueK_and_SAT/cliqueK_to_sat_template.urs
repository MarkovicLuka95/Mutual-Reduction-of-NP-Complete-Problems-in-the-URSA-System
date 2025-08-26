nN = nK*nV;
nClauses = 0;

/*STEP 1: Each position in the clique must be filled*/
for(nj=0; nj<nK; nj++){
	for(ni=0; ni<2*nN; ni++) {
		bC[nClauses][ni] = false;
	}
	for(ni=0; ni<nV; ni++){
		bC[nClauses][nj*2*nV+2*ni] = true;
	}
	nClauses++;
}

/*STEP 2: Each vertex can be in at most one position*/
for(ni=0; ni<nV; ni++){
	for(nj=0; nj<nK; nj++){
		for(nk=nj+1; nk<nK; nk++){
			for(np=0; np<2*nN; np++) {
				bC[nClauses][np] = false;
		  	}
			bC[nClauses][nj*2*nV+2*ni+1] = true;
			bC[nClauses][nk*2*nV+2*ni+1] = true;
			nClauses++;
		}
	}
}

/*STEP 3: Each position can have at most one vertex*/
for(nj=0; nj<nK; nj++){
	for(ni=0; ni<nV; ni++){
		for(nk=ni+1; nk<nV; nk++){
			for(np=0; np<2*nN; np++) {
				bC[nClauses][np] = false;
		  }
			bC[nClauses][nj*2*nV+2*ni+1] = true;
			bC[nClauses][nj*2*nV+2*nk+1] = true;
			nClauses++;
		}
	}
}

/*STEP 4: Vertices in the clique must be connected*/
for(nj=0; nj<nK; nj++){
	for(nl=nj+1; nl<nK; nl++){
		for(ni=0; ni<nV; ni++){
			for(nk=0; nk<nV; nk++){
				if(!bE[ni][nk] && ni!=nk){
					for(np=0; np<2*nN; np++) {
						bC[nClauses][np] = false;
				  }
					bC[nClauses][nj*2*nV+2*ni+1] = true;
					bC[nClauses][nl*2*nV+2*nk+1] = true;
					nClauses++;
				}
			}
		}
	}
}

bB = true;
for(ni=0; ni<nClauses; ni++) {
  b = false;
  for(nj=0; nj<nN; nj++) {
    b ||= ite(bC[ni][2*nj],   bV[nj],  false);
    b ||= ite(bC[ni][2*nj+1],!bV[nj],false);
  }
  bB &&= b;
}
assert(bB);
