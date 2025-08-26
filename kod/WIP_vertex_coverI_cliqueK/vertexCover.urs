/*Exemple from https://www.geeksforgeeks.org/dsa/proof-that-vertex-cover-is-np-complete/*/
nV = 6; 
nK_vertex_cover = 2; 

/*Initialization of an empty graph*/
for(ni=0; ni<nV; ni++) {
  for(nj=0; nj<nV; nj++) {
    bE_vertex[ni][nj] = false;
  }
}

bE_vertex[0][4] = true;
bE_vertex[0][5] = true;
bE_vertex[1][4] = true;
bE_vertex[2][4] = true;
bE_vertex[2][5] = true;
bE_vertex[3][5] = true;
bE_vertex[4][0] = true;
bE_vertex[4][1] = true;
bE_vertex[4][2] = true;
bE_vertex[4][5] = true;
bE_vertex[5][0] = true;
bE_vertex[5][1] = true;
bE_vertex[5][3] = true;
bE_vertex[5][4] = true;

nCount = 0;
b = true;
for(ni=0; ni<nV; ni++) {
  nCount += ite(bBelongs[ni], 1, 0);
  for(nj=ni+1; nj<nV; nj++) {
    b &&= ite((bE_vertex[ni][nj] || bE_vertex[nj][ni]), bBelongs[ni] || bBelongs[nj], true);
  }
}
assert_all(b && nCount <= nK_vertex_cover);

%---------------------------------------------------

