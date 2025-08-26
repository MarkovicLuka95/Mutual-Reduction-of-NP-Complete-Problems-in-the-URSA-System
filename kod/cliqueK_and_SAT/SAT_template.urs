bB = true;
for(ni=0; ni<nClauses; ni++) {
  b = false;
  for(nj=0; nj<nN; nj++) {
    b ||= ite(bC[ni][2*nj],   bV[nj],  false);
    b ||= ite(bC[ni][2*nj+1], !bV[nj], false);
  }
  bB &&= b;
}
assert(bB);

