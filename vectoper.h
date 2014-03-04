/* === Vector Operations === */
/* Some operations like scalar product, linear operations, etc */
/* copyrights www.adrutsa.ru */

#ifndef VECTOPER_H
#define VECTOPER_H

#include "math.h"
#define VECTOR_TYPE float 

void ad_vo_copy(long int n, VECTOR_TYPE * u, VECTOR_TYPE * v); /* u = v */

VECTOR_TYPE ad_vo_scalprod(long int n, VECTOR_TYPE * v, VECTOR_TYPE *u); /* return u*v */

void ad_vo_addline(long int n, VECTOR_TYPE * v, VECTOR_TYPE * u, VECTOR_TYPE c); /* v = v + u*c */

void ad_vo_scalmult(long int n, VECTOR_TYPE * v, VECTOR_TYPE c); /* v = v*c */

VECTOR_TYPE ad_vo_norm_l2(long int n, VECTOR_TYPE * v); /* l_2 norm of the vector v */

VECTOR_TYPE ad_vo_norm_l1(long int n, VECTOR_TYPE * v); /* l_1 norm of the vector v */

VECTOR_TYPE ad_vo_norm_max(long int n, VECTOR_TYPE * v); /* max norm (l_infinity norm) of the vector v */

#endif 
