// --> COMMON SHADER START
#define PI 3.14159265359

float rand(vec3 p){return fract(sin(dot(p, vec3(87.1313, 31.5757, 17.2323))+sin(dot(p, vec3(15.1313, 67.4747, 76.1313)))) * 45189.3257);}
float rand(vec4 p){return fract(sin(dot(p, vec4(87.1313, 31.5757, 17.2323, 58.6767))+sin(dot(p, vec4(15.1313, 67.4747, 76.1313, 21.5757)))) * 45189.3257);}

float mod289(float x){return x - floor(x * (1.0 / 289.0)) * 289.0;}
vec4 mod289(vec4 x){return x - floor(x * (1.0 / 289.0)) * 289.0;}
vec4 perm(vec4 x){return mod289(((x * 34.0) + 1.0) * x);}
float noise(vec3 p){vec3 a = floor(p);vec3 d = p - a;d = d * d * (3.0 - 2.0 * d);vec4 b = a.xxyy + vec4(0.0, 1.0, 0.0, 1.0);vec4 k1 = perm(b.xyxy);vec4 k2 = perm(k1.xyxy + b.zzww);vec4 c = k2 + a.zzzz;vec4 k3 = perm(c);vec4 k4 = perm(c + 1.0);vec4 o1 = fract(k3 * (1.0 / 41.0));vec4 o2 = fract(k4 * (1.0 / 41.0));vec4 o3 = o2 * d.z + o1 * (1.0 - d.z);vec2 o4 = o3.yw * d.x + o3.xz * (1.0 - d.x);return o4.y * d.y + o4.x * (1.0 - d.y);}
vec2 rotate(vec2 p, float a){return mat2(cos(a), -sin(a), sin(a), cos(a)) * p;}


float dot2(in vec2 v ) { return dot(v,v); }
float dot2(in vec3 v ) { return dot(v,v); }

float hue2rgb(float f1, float f2, float hue) {if (hue < 0.0) hue += 1.0; else if (hue > 1.0) hue -= 1.0; float res; if ((6.0 * hue) < 1.0) res = f1 + (f2 - f1) * 6.0 * hue; else if ((2.0 * hue) < 1.0) res = f2; else if ((3.0 * hue) < 2.0) res = f1 + (f2 - f1) * ((2.0 / 3.0) - hue) * 6.0; else res = f1; return res;}
vec3 hsl2rgb(vec3 hsl) {vec3 rgb;if (hsl.y == 0.0) {rgb = vec3(hsl.z);} else {float f2; if (hsl.z < 0.5)f2 = hsl.z * (1.0 + hsl.y);else f2 = hsl.z + hsl.y - hsl.y * hsl.z;float f1 = 2.0 * hsl.z - f2;rgb.r = hue2rgb(f1, f2, hsl.x + (1.0/3.0));rgb.g = hue2rgb(f1, f2, hsl.x);rgb.b = hue2rgb(f1, f2, hsl.x - (1.0/3.0));} return rgb;}
vec3 hsl2rgb(float h, float s, float l) {return hsl2rgb(vec3(h, s, l));}
vec3 rgb2hsl(vec3 color) { vec3 hsl; float fmin = min(min(color.r, color.g), color.b); float fmax = max(max(color.r, color.g), color.b); float delta = fmax - fmin; hsl.z = (fmax + fmin) / 2.0; if (delta == 0.0) { hsl.x = 0.0; hsl.y = 0.0; } else { if (hsl.z < 0.5) hsl.y = delta / (fmax + fmin); else hsl.y = delta / (2.0 - fmax - fmin); float deltaR = (((fmax - color.r) / 6.0) + (delta / 2.0)) / delta; float deltaG = (((fmax - color.g) / 6.0) + (delta / 2.0)) / delta; float deltaB = (((fmax - color.b) / 6.0) + (delta / 2.0)) / delta; if (color.r == fmax) hsl.x = deltaB - deltaG; else if (color.g == fmax) hsl.x = (1.0 / 3.0) + deltaR - deltaB; else if (color.b == fmax) hsl.x = (2.0 / 3.0) + deltaG - deltaR; if (hsl.x < 0.0) hsl.x += 1.0; else if (hsl.x > 1.0) hsl.x -= 1.0; } return hsl; }

float mono(vec3 col){return (clamp(col.r, .0, 1.) + clamp(col.g, .0, 1.) + clamp(col.b, .0, 1.)) / 3.;}

vec4 permute(vec4 x){return mod(((x*34.0)+1.0)*x, 289.0);}
vec4 taylorInvSqrt(vec4 r){return 1.79284291400159 - 0.85373472095314 * r;}
float snoise(vec3 v){ const vec2  C = vec2(1.0/6.0, 1.0/3.0) ; const vec4  D = vec4(0.0, 0.5, 1.0, 2.0);vec3 i  = floor(v + dot(v, C.yyy) );vec3 x0 =   v - i + dot(i, C.xxx) ;vec3 g = step(x0.yzx, x0.xyz);vec3 l = 1.0 - g;vec3 i1 = min( g.xyz, l.zxy );vec3 i2 = max( g.xyz, l.zxy );vec3 x1 = x0 - i1 + 1.0 * C.xxx;vec3 x2 = x0 - i2 + 2.0 * C.xxx;vec3 x3 = x0 - 1. + 3.0 * C.xxx;i = mod(i, 289.0 ); vec4 p = permute( permute( permute( i.z + vec4(0.0, i1.z, i2.z, 1.0 ))+ i.y + vec4(0.0, i1.y, i2.y, 1.0 )) + i.x + vec4(0.0, i1.x, i2.x, 1.0 ));float n_ = 1.0/7.0;vec3  ns = n_ * D.wyz - D.xzx;vec4 j = p - 49.0 * floor(p * ns.z *ns.z);vec4 x_ = floor(j * ns.z);vec4 y_ = floor(j - 7.0 * x_ );vec4 x = x_ *ns.x + ns.yyyy;vec4 y = y_ *ns.x + ns.yyyy;vec4 h = 1.0 - abs(x) - abs(y);vec4 b0 = vec4( x.xy, y.xy );vec4 b1 = vec4( x.zw, y.zw );vec4 s0 = floor(b0)*2.0 + 1.0;vec4 s1 = floor(b1)*2.0 + 1.0;vec4 sh = -step(h, vec4(0.0));vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy ;vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww ;vec3 p0 = vec3(a0.xy,h.x);vec3 p1 = vec3(a0.zw,h.y);vec3 p2 = vec3(a1.xy,h.z);vec3 p3 = vec3(a1.zw,h.w);vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2, p2), dot(p3,p3)));p0 *= norm.x;p1 *= norm.y;p2 *= norm.z;p3 *= norm.w;vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);m = m * m;return 42.0 * dot( m*m, vec4( dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3) ) );}

float sdSegment( in vec2 p, in vec2 a, in vec2 b ){ vec2 pa = p-a, ba = b-a; float h = clamp( dot(pa,ba)/dot(ba,ba), 0.0, 1.0 ); return length( pa - ba*h );}
float sdBox( in vec2 p, in vec2 b ){ vec2 d = abs(p)-b; return length(max(d,0.0)) + min(max(d.x,d.y),0.0);}
float sdSphere( vec3 p, float s ){ return length(p)-s;}
float sdBox( vec3 p, vec3 b ){ vec3 q = abs(p) - b; return length(max(q,0.0)) + min(max(q.x,max(q.y,q.z)),0.0);}
float sdCircle(vec2 p, float r) { return length(p) - r;}

float sdEllipse( in vec2 p, in vec2 ab )
{
    if( ab.x==ab.y ) return length(p)-ab.x;
    
    p = abs(p); if( p.x > p.y ) {p=p.yx;ab=ab.yx;}
    float l = ab.y*ab.y - ab.x*ab.x;
    float m = ab.x*p.x/l;      float m2 = m*m; 
    float n = ab.y*p.y/l;      float n2 = n*n; 
    float c = (m2+n2-1.0)/3.0; float c3 = c*c*c;
    float q = c3 + m2*n2*2.0;
    float d = c3 + m2*n2;
    float g = m + m*n2;
    float co;
    if( d<0.0 )
    {
        float h = acos(q/c3)/3.0;
        float s = cos(h);
        float t = sin(h)*sqrt(3.0);
        float rx = sqrt( -c*(s + t + 2.0) + m2 );
        float ry = sqrt( -c*(s - t + 2.0) + m2 );
        co = (ry+sign(l)*rx+abs(g)/(rx*ry)- m)/2.0;
    }
    else
    {
        float h = 2.0*m*n*sqrt( d );
        float s = sign(q+h)*pow(abs(q+h), 1.0/3.0);
        float u = sign(q-h)*pow(abs(q-h), 1.0/3.0);
        float rx = -s - u - c*4.0 + 2.0*m2;
        float ry = (s - u)*sqrt(3.0);
        float rm = sqrt( rx*rx + ry*ry );
        co = (ry/sqrt(rm-rx)+2.0*g/rm-m)/2.0;
    }
    vec2 r = ab * vec2(co, sqrt(1.0-co*co));
    return length(r-p) * sign(p.y-r.y);
}

float sdEllipsoid( vec3 p, vec3 r )
{
  float k0 = length(p/r);
  float k1 = length(p/(r*r));
  return k0*(k0-1.0)/k1;
}

float sdPyramid( vec3 p, float h )
{
  float m2 = h*h + 0.25;
    
  p.xz = abs(p.xz);
  p.xz = (p.z>p.x) ? p.zx : p.xz;
  p.xz -= 0.5;

  vec3 q = vec3( p.z, h*p.y - 0.5*p.x, h*p.x + 0.5*p.y);
   
  float s = max(-q.x,0.0);
  float t = clamp( (q.y-0.5*p.z)/(m2+0.25), 0.0, 1.0 );
    
  float a = m2*(q.x+s)*(q.x+s) + q.y*q.y;
  float b = m2*(q.x+0.5*t)*(q.x+0.5*t) + (q.y-m2*t)*(q.y-m2*t);
    
  float d2 = min(q.y,-q.x*m2-q.y*0.5) > 0.0 ? 0.0 : min(a,b);
    
  return sqrt( (d2+q.z*q.z)/m2 ) * sign(max(q.z,-p.y));
}

float sdOctahedron( vec3 p, float s )
{
  p = abs(p);
  float m = p.x+p.y+p.z-s;
  vec3 q;
       if( 3.0*p.x < m ) q = p.xyz;
  else if( 3.0*p.y < m ) q = p.yzx;
  else if( 3.0*p.z < m ) q = p.zxy;
  else return m*0.57735027;
    
  float k = clamp(0.5*(q.z-q.y+s),0.0,s); 
  return length(vec3(q.x,q.y-s+k,q.z-k)); 
}

float smin( float a, float b, float k )
{
    float h = max( k-abs(a-b), 0.0 )/k;
    return min( a, b ) - h*h*k*(1.0/4.0);
}

float bezierBlend(float t) {
    return t * t * (3.0 - 2.0 * t);
}

float sdCappedCylinder( vec3 p, float h, float r )
{
  vec2 d = abs(vec2(length(p.xz),p.y)) - vec2(r,h);
  return min(max(d.x,d.y),0.0) + length(max(d,0.0));
}

float sdCapsule( vec3 p, vec3 a, vec3 b, float r )
{
  vec3 pa = p - a, ba = b - a;
  float h = clamp( dot(pa,ba)/dot(ba,ba), 0.0, 1.0 );
  return length( pa - ba*h ) - r;
}

float sdVerticalCapsule( vec3 p, float h, float r )
{
  p.y -= clamp( p.y, 0.0, h );
  return length( p ) - r;
}

float sdCappedCone( in vec3 p, in float h, in float r1, in float r2 )
{
    vec2 q = vec2( length(p.xz), p.y );
    
    vec2 k1 = vec2(r2,h);
    vec2 k2 = vec2(r2-r1,2.0*h);
    vec2 ca = vec2(q.x-min(q.x,(q.y < 0.0)?r1:r2), abs(q.y)-h);
    vec2 cb = q - k1 + k2*clamp( dot(k1-q,k2)/dot2(k2), 0.0, 1.0 );
    float s = (cb.x < 0.0 && ca.y < 0.0) ? -1.0 : 1.0;
    return s*sqrt( min(dot2(ca),dot2(cb)) );
}

float sdRoundCone( vec3 p, vec3 a, vec3 b, float r1, float r2 )
{
  vec3  ba = b - a;
  float l2 = dot(ba,ba);
  float rr = r1 - r2;
  float a2 = l2 - rr*rr;
  float il2 = 1.0/l2;
    
  vec3 pa = p - a;
  float y = dot(pa,ba);
  float z = y - l2;
  float x2 = dot2( pa*l2 - ba*y );
  float y2 = y*y*l2;
  float z2 = z*z*l2;

  // single square root!
  float k = sign(rr)*rr*rr*x2;
  if( sign(z)*a2*z2>k ) return  sqrt(x2 + z2)        *il2 - r2;
  if( sign(y)*a2*y2<k ) return  sqrt(x2 + y2)        *il2 - r1;
                        return (sqrt(x2*a2*il2)+y*rr)*il2 - r1;
}

float sdCappedTorus( vec3 p, vec2 sc, float ra, float rb)
{
  p.x = abs(p.x);
  float k = (sc.y*p.x>sc.x*p.y) ? dot(p.xy,sc) : length(p.xy);
  return sqrt( dot(p,p) + ra*ra - 2.0*ra*k ) - rb;
}

float sdLink( vec3 p, float le, float r1, float r2 )
{
  vec3 q = vec3( p.x, max(abs(p.y)-le,0.0), p.z );
  return length(vec2(length(q.xy)-r1,q.z)) - r2;
}

float sdCone( vec3 p, vec2 c, float h )
{
  // c is the sin/cos of the angle, h is height
  // Alternatively pass q instead of (c,h),
  // which is the point at the base in 2D
  vec2 q = h*vec2(c.x/c.y,-1.0);
    
  vec2 w = vec2( length(p.xz), p.y );
  vec2 a = w - q*clamp( dot(w,q)/dot(q,q), 0.0, 1.0 );
  vec2 b = w - q*vec2( clamp( w.x/q.x, 0.0, 1.0 ), 1.0 );
  float k = sign( q.y );
  float d = min(dot( a, a ),dot(b, b));
  float s = max( k*(w.x*q.y-w.y*q.x),k*(w.y-q.y)  );
  return sqrt(d)*sign(s);
}

// float sdCone( vec3 p, vec2 c, float h )
// {
//   float q = length(p.xz);
//   return max(dot(c.xy,vec2(q,p.y)),-h-p.y);
// }

float sdPentagon( in vec2 p, in float r )
{
    const vec3 k = vec3(0.809016994,0.587785252,0.726542528);
    p.x = abs(p.x);
    p -= 2.0*min(dot(vec2(-k.x,k.y),p),0.0)*vec2(-k.x,k.y);
    p -= 2.0*min(dot(vec2( k.x,k.y),p),0.0)*vec2( k.x,k.y);
    p -= vec2(clamp(p.x,-r*k.z,r*k.z),r);    
    return length(p)*sign(p.y);
}

float sdPentagram(in vec2 p, in float r )
{
    const float k1x = 0.809016994; // cos(π/ 5) = ¼(√5+1)
    const float k2x = 0.309016994; // sin(π/10) = ¼(√5-1)
    const float k1y = 0.587785252; // sin(π/ 5) = ¼√(10-2√5)
    const float k2y = 0.951056516; // cos(π/10) = ¼√(10+2√5)
    const float k1z = 0.726542528; // tan(π/ 5) = √(5-2√5)
    const vec2  v1  = vec2( k1x,-k1y);
    const vec2  v2  = vec2(-k1x,-k1y);
    const vec2  v3  = vec2( k2x,-k2y);
    
    p.x = abs(p.x);
    p -= 2.0*max(dot(v1,p),0.0)*v1;
    p -= 2.0*max(dot(v2,p),0.0)*v2;
    p.x = abs(p.x);
    p.y -= r;
    return length(p-v3*clamp(dot(p,v3),0.0,k1z*r))
           * sign(p.y*v3.x-p.x*v3.y);
}

vec3 col_palette( in float t, in vec3 a, in vec3 b, in vec3 c, in vec3 d ){return a + b*cos( 6.28318*(c*t+d) );}

float sdTorus( vec3 p, vec2 t )
{
  vec2 q = vec2(length(p.xz)-t.x,p.y);
  return length(q)-t.y;
}

float sdTriPrism( vec3 p, vec2 h )
{
  vec3 q = abs(p);
  return max(q.z-h.y,max(q.x*0.866025+p.y*0.5,-p.y)-h.x*0.5);
}

vec4 opElongate( in vec3 p, in vec3 h )
{
    vec3 q = abs(p)-h;
    return vec4( max(q,0.0), min(max(q.x,max(q.y,q.z)),0.0) );
}

float opUnion( float d1, float d2 )
{
    return min(d1,d2);
}
float opSubtraction( float d1, float d2 )
{
    return max(-d1,d2);
}
float opIntersection( float d1, float d2 )
{
    return max(d1,d2);
}
float opXor(float d1, float d2 )
{
    return max(min(d1,d2),-max(d1,d2));
}

float opSmoothUnion( float d1, float d2, float k )
{
    float h = clamp( 0.5 + 0.5*(d2-d1)/k, 0.0, 1.0 );
    return mix( d2, d1, h ) - k*h*(1.0-h);
}

float opSmoothSubtraction( float d1, float d2, float k )
{
    float h = clamp( 0.5 - 0.5*(d2+d1)/k, 0.0, 1.0 );
    return mix( d2, -d1, h ) + k*h*(1.0-h);
}

float opSmoothIntersection( float d1, float d2, float k )
{
    float h = clamp( 0.5 - 0.5*(d2-d1)/k, 0.0, 1.0 );
    return mix( d2, d1, h ) + k*h*(1.0-h);
}

float sdHelix( in vec3 p, float fr, float r1, float r2 )
{
    vec2  nline = vec2(fr, 6.283185*r1 );
    vec2  pline = vec2(nline.y, -nline.x);
    float repeat = nline.x*nline.y;

    vec2  pc = vec2(p.x,r1*atan(p.y,p.z));              // to cylindrical

    vec2  pp = vec2( dot(pc,pline),                     // project to line
                     dot(pc,nline));
    
    pp.x = round(pp.x/repeat)*repeat;                   // repeat in x

    vec2 qc = (nline*pp.y+pline*pp.x)/dot(nline,nline); // un project to cylindrical
    qc.y /= r1;
    
    vec3 q = vec3(qc.x, sin(qc.y)*r1, cos(qc.y)*r1 );   // to cartesian
        
    return length(p-q)-r2;
}

float median(float r, float g, float b) {
    return max(min(r, g), min(max(r, g), b));
}

// https://www.shadertoy.com/view/tlsGzn
float extrudeDist(float d, float w, float y) {
    return length(vec2(max(d, 0.), y - clamp(y, -w, w))) + min(max(d, abs(y) - w), 0.);
}

float sdEquilateralTriangle( in vec2 p, in float r )
{
    const float k = sqrt(3.0);
    p.x = abs(p.x) - r;
    p.y = p.y + r/k;
    if( p.x+k*p.y>0.0 ) p = vec2(p.x-k*p.y,-k*p.x-p.y)/2.0;
    p.x -= clamp( p.x, -2.0*r, 0.0 );
    return -length(p)*sign(p.y);
}

float sdArc( in vec2 p, in vec2 sc, in float ra, float rb )
{
    // sc is the sin/cos of the arc's aperture
    p.x = abs(p.x);
    return ((sc.y*p.x>sc.x*p.y) ? length(p-sc*ra) : 
                                  abs(length(p)-ra)) - rb;
}

float sdLine( in vec2 p, in vec2 a, in vec2 b, float w ){ 
    vec2 pa = p-a, ba = b-a;
    vec2 dir = normalize(ba);
    float l = dot(pa, dir);
    float bal = length(ba);
    vec2 h = l * dir + a;
    float dst = length(h-p)-w;
    // dst = max(dst,-l-w);
    // dst = max(dst,l-bal-w);
    dst = max(dst,-l);
    dst = max(dst,l-bal);
    
    return dst;
}

// --> COMMON SHADER END