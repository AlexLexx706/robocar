#include  "vectoper.h"

void ad_vo_copy(long int n, VECTOR_TYPE * u, VECTOR_TYPE * v)
{
    long int i;
    for(i=0;i<n;i++) u[i]=v[i];
}

VECTOR_TYPE ad_vo_scalprod(long int n, VECTOR_TYPE * v, VECTOR_TYPE *u)
{
    long int i;
    VECTOR_TYPE s=0.;
    for(i=0;i<n;i++) s+=v[i]*u[i];
    return s;
}

void ad_vo_addline(long int n, VECTOR_TYPE * v, VECTOR_TYPE * u, VECTOR_TYPE c)
{
    long int i;
    for(i=0;i<n;i++) v[i]+=u[i]*c;
}


void ad_vo_scalmult(long int n, VECTOR_TYPE * v, VECTOR_TYPE c)
{
    long int i;
    for(i=0;i<n;i++) v[i]*=c;
}

VECTOR_TYPE ad_vo_norm_l2(long int n, VECTOR_TYPE * v)
{
    long int i;
    VECTOR_TYPE s=0.;
    for(i=0;i<n;i++) s+=v[i]*v[i];
    return sqrt(s);
}

VECTOR_TYPE ad_vo_norm_l1(long int n, VECTOR_TYPE * v)
{
    long int i;
    VECTOR_TYPE s=0.;
    for(i=0;i<n;i++) s+=fabs(v[i]);
    return s;
}

VECTOR_TYPE ad_vo_norm_max(long int n, VECTOR_TYPE * v)
{
    long int i;
    VECTOR_TYPE s=fabs(v[0]);
    for(i=0;i<n;i++) if (s<fabs(v[i])) s=fabs(v[i]);
    return s;
}