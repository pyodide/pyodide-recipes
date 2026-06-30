/*
 * Functional check for the BLIS WebAssembly build.
 *
 * Exercises one routine from each BLAS level plus the complex Givens
 * rotation wrappers added by patch 0002, then compares every result
 * against values independently computed with native SciPy. See the
 * "To verify" block in test_libblis.py for the matching SciPy code.
 */

#include <stdio.h>
#include <math.h>
#include "cblas.h"

static int failures = 0;

static void check(const char *name, double got, double want)
{
    double tol = 1e-9;
    if (fabs(got - want) > tol) {
        printf("FAIL %s: got %.12g want %.12g\n", name, got, want);
        failures += 1;
    } else {
        printf("ok   %s = %.6g\n", name, got);
    }
}

int main(void)
{
    /* Level 1 */
    double x[4] = {1.0, 2.0, 3.0, 4.0};
    double y[4] = {5.0, 6.0, 7.0, 8.0};
    check("L1 ddot", cblas_ddot(4, x, 1, y, 1), 70.0);

    double v[2] = {3.0, 4.0};
    check("L1 dnrm2", cblas_dnrm2(2, v, 1), 5.0);

    double w[3] = {-1.0, 2.0, -3.0};
    check("L1 dasum", cblas_dasum(3, w, 1), 6.0);

    double ax[3] = {1.0, 2.0, 3.0};
    double ay[3] = {4.0, 5.0, 6.0};
    cblas_daxpy(3, 2.0, ax, 1, ay, 1);
    check("L1 daxpy[0]", ay[0], 6.0);
    check("L1 daxpy[1]", ay[1], 9.0);
    check("L1 daxpy[2]", ay[2], 12.0);

    /* Level 2: y = A x with A row major 3x3 of 1..9 and x all ones */
    double A[9] = {1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0};
    double xv[3] = {1.0, 1.0, 1.0};
    double yv[3] = {0.0, 0.0, 0.0};
    cblas_dgemv(CblasRowMajor, CblasNoTrans, 3, 3, 1.0, A, 3, xv, 1, 0.0, yv, 1);
    check("L2 dgemv[0]", yv[0], 6.0);
    check("L2 dgemv[1]", yv[1], 15.0);
    check("L2 dgemv[2]", yv[2], 24.0);

    /* Level 3: C = A B with row major 2x2 inputs */
    double Am[4] = {1.0, 2.0, 3.0, 4.0};
    double Bm[4] = {5.0, 6.0, 7.0, 8.0};
    double Cm[4] = {0.0, 0.0, 0.0, 0.0};
    cblas_dgemm(CblasRowMajor, CblasNoTrans, CblasNoTrans, 2, 2, 2,
                1.0, Am, 2, Bm, 2, 0.0, Cm, 2);
    check("L3 dgemm[0][0]", Cm[0], 19.0);
    check("L3 dgemm[0][1]", Cm[1], 22.0);
    check("L3 dgemm[1][0]", Cm[2], 43.0);
    check("L3 dgemm[1][1]", Cm[3], 50.0);

    /* Complex Givens from patch 0002: zrotg with a = 1 + 1i and b = 0
     * leaves r = a, cosine = 1, sine = 0. Layout is real then imag. */
    double za[2] = {1.0, 1.0};
    double zb[2] = {0.0, 0.0};
    double cc = 0.0;
    double ss[2] = {0.0, 0.0};
    cblas_zrotg(za, zb, &cc, ss);
    check("cplx zrotg c", cc, 1.0);
    check("cplx zrotg s.re", ss[0], 0.0);
    check("cplx zrotg s.im", ss[1], 0.0);
    check("cplx zrotg r.re", za[0], 1.0);
    check("cplx zrotg r.im", za[1], 1.0);

    /* csrot from patch 0002: apply a real plane rotation with c = 0 and
     * s = 1 to two complex vectors. That swaps x into y and negates the
     * old y into x. Start x = 1 + 2i, y = 3 + 4i. */
    float cx[2] = {1.0f, 2.0f};
    float cy[2] = {3.0f, 4.0f};
    cblas_csrot(1, cx, 1, cy, 1, 0.0f, 1.0f);
    check("cplx csrot x.re", cx[0], 3.0);
    check("cplx csrot x.im", cx[1], 4.0);
    check("cplx csrot y.re", cy[0], -1.0);
    check("cplx csrot y.im", cy[1], -2.0);

    printf(failures ? "\nRESULT: FAILED (%d)\n" : "\nRESULT: PASSED\n", failures);
    return failures ? 1 : 0;
}
