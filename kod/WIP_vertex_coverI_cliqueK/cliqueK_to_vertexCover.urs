nV = 6; 
nK = 4; 

/*Initialization of an empty graph*/
for(ni=0; ni<nV; ni++) {
  for(nj=0; nj<nV; nj++) {
    bE[ni][nj] = false;
  }
}

bE[0][1] = true;
bE[0][2] = true;
bE[0][3] = true;
bE[1][0] = true;
bE[1][2] = true;
bE[1][3] = true;
bE[1][5] = true;
bE[2][0] = true;
bE[2][1] = true;
bE[2][3] = true;
bE[3][0] = true;
bE[3][1] = true;
bE[3][2] = true;
bE[3][4] = true;
bE[4][3] = true;
bE[5][2] = true;

/*Reduction from clique to vertexCover*/
for(ni=0; ni<nV; ni++) {
  for(nj=0; nj<nV; nj++) {
    if(ni == nj) {
      bE_vertex[ni][nj] = false;
    } else {
      bE_vertex[ni][nj] = !bE[ni][nj];
    }
  }
}

nK_vertex_cover = nV - nK;

nCount = 0;
b = true;
for(ni=0; ni<nV; ni++) {
  nCount += ite(bBelongs[ni], 1, 0);
  for(nj=ni+1; nj<nV; nj++) {
    b &&= ite((bE_vertex[ni][nj] || bE_vertex[nj][ni]), bBelongs[ni] || bBelongs[nj], true);
  }
}
assert_all(b && nCount <= nK_vertex_cover);
