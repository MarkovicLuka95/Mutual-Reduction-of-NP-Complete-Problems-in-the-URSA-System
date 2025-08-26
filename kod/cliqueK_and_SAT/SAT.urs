nN = 3;
nClauses = 3;

for(ni=0; ni<nClauses; ni++) {
  for(nj=0; nj<2*nN; nj++) {
    bC[ni][nj] = false;
  }
}

bC[0][0] = true;
bC[0][2] = true;
bC[1][1] = true;
bC[1][3] = true;
bC[2][0] = true;
bC[2][4] = true;

bB = true;
for(ni=0; ni<nClauses; ni++) {
  b = false;
  for(nj=0; nj<nN; nj++) {
    b ||= ite(bC[ni][2*nj],   bV[nj],  false);
    b ||= ite(bC[ni][2*nj+1], !bV[nj], false);
  }
  bB &&= b;
}
assert_all(bB);

