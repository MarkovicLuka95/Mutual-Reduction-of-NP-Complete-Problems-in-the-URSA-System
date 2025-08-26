nV = 6; 
nK = 3; 

/*Inicialization of empty graph*/
for(ni=0; ni<nV; ni++) {
  for(nj=0; nj<nV; nj++) {
    bE[ni][nj] = false;
  }
}

bE[0][3] = true;
bE[0][4] = true;
bE[0][5] = true;
bE[1][2] = true;
bE[1][4] = true;
bE[1][5] = true;
bE[2][1] = true;
bE[2][5] = true;
bE[3][0] = true;
bE[3][4] = true;
bE[3][5] = true;
bE[4][0] = true;
bE[4][1] = true;
bE[4][3] = true;
bE[5][0] = true;
bE[5][1] = true;
bE[5][2] = true;
bE[5][3] = true;

nCount = 0;
b = true;
for(ni=0; ni<nV; ni++) {
  nCount += ite(bBelongs[ni], 1, 0);
  for(nj=ni+1; nj<nV; nj++) {
    b &&= ite(bBelongs[ni] && bBelongs[nj], (bE[ni][nj] || bE[nj][ni]), true);
  }
}
assert_all(b && nCount >= nK);

%---------------------------------------------------

