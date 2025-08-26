/* STEP 0: inicijalizacija */
nNodes = 0;
for (ni = 0; ni < nClauses; ni++) {
  nLen[ni] = 0; /*number of literals in clause i*/
}

/* STEP 1: create nodes ONLY for literals that actually exist in clauses */
for (ni = 0; ni < nClauses; ni++) {
  for (nl = 0; nl < 2*nN; nl++) {
    nNodeOf[ni][nLen[ni]] = ite(bC[ni][nl], nNodes, nNodeOf[ni][nLen[ni]]); /* global node index*/
    nLitOfNode[nNodes]    = ite(bC[ni][nl], nl,     nLitOfNode[nNodes]); /* literal id that this global node represents */
    nClauseOfNode[nNodes] = ite(bC[ni][nl], ni,     nClauseOfNode[nNodes]); /* nClauseOfNode[node] = clause index this node belongs to */


    nLen[ni] += ite(bC[ni][nl], 1, 0);
    nNodes   += ite(bC[ni][nl], 1, 0);
  }
}

/* STEP 3: initialize adjacency matrix */
nV = nNodes;
nK = nClauses;
for (nu = 0; nu < nV; nu++) {
  for (nv = 0; nv < nV; nv++) {
    bE[nu][nv] = false;
  }
}

/* STEP 4: add edges between literals of different clauses */
for (nci = 0; nci < nClauses; nci++) {
  for (ncj = nci + 1; ncj < nClauses; ncj++) {

    for (nti = 0; nti < nLen[nci]; nti++) {
      nv   = nNodeOf[nci][nti];
      nl1  = nLitOfNode[nv];
      nVar1 = nl1 >> 1;     /* variable index of literal */
      nPol1 = nl1 & 1;      /* polarity: 0=positive, 1=negative */

      for (ntj = 0; ntj < nLen[ncj]; ntj++) {
        nu   = nNodeOf[ncj][ntj];
        nl2  = nLitOfNode[nu];
        nVar2 = nl2 >> 1;
        nPol2 = nl2 & 1;

        bConflict = (nVar1 == nVar2) && (nPol1 != nPol2);

        bE[nv][nu] = ite(!bConflict, true, bE[nv][nu]);
        bE[nu][nv] = ite(!bConflict, true, bE[nu][nv]);
      }
    }
  }
}

/* STEP 6: check if chosen nodes form a clique */
bValid = true;
for (nu = 0; nu < nV; nu++) {
  nCount += ite(bBelongs[nu], 1, 0);
  for (nv = nu + 1; nv < nV; nv++) {
    bValid = bValid && ite(bBelongs[nu] && bBelongs[nv], bE[nu][nv], true);
    /* if both nu and nv are chosen → require edge between them; otherwise → no condition */
  }
}

assert( bValid && (nCount == nK) );


