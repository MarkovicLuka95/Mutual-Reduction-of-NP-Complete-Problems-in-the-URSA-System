nCount = 0;
b = true;
for(ni=0; ni<nV; ni++) {
  nCount += ite(bBelongs[ni], 1, 0);
  for(nj=ni+1; nj<nV; nj++) {
    b &&= ite(bBelongs[ni] && bBelongs[nj], (bE[ni][nj] || bE[nj][ni]), true);
  }
}
assert(b && nCount >= nK);
