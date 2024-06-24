/**
 * Bundled by jsDelivr using Rollup v2.79.1 and Terser v5.19.2.
 * Original file: /npm/vega-time@2.1.2/build/vega-time.module.js
 *
 * Do NOT use SRI with dynamically generated files! More information: https://www.jsdelivr.com/using-sri-with-dynamic-files
 */
import{array as t,error as e,hasOwnProperty as n,extend as r,span as o,peek as u,toSet as i,constant as c,zero as s,one as a}from"../vega-util@1.17.2/_esm.js";import{timeYear as l,timeMonth as f,timeWeek as g,timeDay as m,timeHour as D,timeMinute as T,timeSecond as U,timeMillisecond as h,utcYear as C,utcMonth as d,utcWeek as M,utcDay as y,utcHour as Y,utcMinute as w,utcSecond as p,utcMillisecond as F}from"../d3-time@3.1.0/_esm.js";import{bisector as $,tickStep as v}from"../d3-array@3.2.4/_esm.js";const b="year",x="quarter",H="month",S="week",j="date",k="day",q="dayofyear",I="hours",B="minutes",E="seconds",L="milliseconds",Q=[b,x,H,S,j,k,q,I,B,E,L],W=Q.reduce(((t,e,n)=>(t[e]=1+n,t)),{});function z(r){const o=t(r).slice(),u={};o.length||e("Missing time unit."),o.forEach((t=>{n(W,t)?u[t]=1:e(`Invalid time unit: ${t}.`)}));return(u[S]||u[k]?1:0)+(u[x]||u[H]||u[j]?1:0)+(u[q]?1:0)>1&&e(`Incompatible time units: ${r}`),o.sort(((t,e)=>W[t]-W[e])),o}const A={[b]:"%Y ",[x]:"Q%q ",[H]:"%b ",[j]:"%d ",[S]:"W%U ",[k]:"%a ",[q]:"%j ",[I]:"%H:00",[B]:"00:%M",[E]:":%S",[L]:".%L",[`${b}-${H}`]:"%Y-%m ",[`${b}-${H}-${j}`]:"%Y-%m-%d ",[`${I}-${B}`]:"%H:%M"};function G(t,e){const n=r({},A,e),o=z(t),u=o.length;let i,c,s="",a=0;for(a=0;a<u;)for(i=o.length;i>a;--i)if(c=o.slice(a,i).join("-"),null!=n[c]){s+=n[c],a=i;break}return s.trim()}const J=new Date;function K(t){return J.setFullYear(t),J.setMonth(0),J.setDate(1),J.setHours(0,0,0,0),J}function N(t){return P(new Date(t))}function O(t){return R(new Date(t))}function P(t){return m.count(K(t.getFullYear())-1,t)}function R(t){return g.count(K(t.getFullYear())-1,t)}function V(t){return K(t).getDay()}function X(t,e,n,r,o,u,i){if(0<=t&&t<100){const c=new Date(-1,e,n,r,o,u,i);return c.setFullYear(t),c}return new Date(t,e,n,r,o,u,i)}function Z(t){return tt(new Date(t))}function _(t){return et(new Date(t))}function tt(t){const e=Date.UTC(t.getUTCFullYear(),0,1);return y.count(e-1,t)}function et(t){const e=Date.UTC(t.getUTCFullYear(),0,1);return M.count(e-1,t)}function nt(t){return J.setTime(Date.UTC(t,0,1)),J.getUTCDay()}function rt(t,e,n,r,o,u,i){if(0<=t&&t<100){const t=new Date(Date.UTC(-1,e,n,r,o,u,i));return t.setUTCFullYear(n.y),t}return new Date(Date.UTC(t,e,n,r,o,u,i))}function ot(t,e,n,r,o){const l=e||1,f=u(t),g=(t,e,o)=>function(t,e,n,r){const o=n<=1?t:r?(e,o)=>r+n*Math.floor((t(e,o)-r)/n):(e,r)=>n*Math.floor(t(e,r)/n);return e?(t,n)=>e(o(t,n),n):o}(n[o=o||t],r[o],t===f&&l,e),m=new Date,D=i(t),T=D[b]?g(b):c(2012),U=D[H]?g(H):D[x]?g(x):s,h=D[S]&&D[k]?g(k,1,S+k):D[S]?g(S,1):D[k]?g(k,1):D[j]?g(j,1):D[q]?g(q,1):a,C=D[I]?g(I):s,d=D[B]?g(B):s,M=D[E]?g(E):s,y=D[L]?g(L):s;return function(t){m.setTime(+t);const e=T(m);return o(e,U(m),h(m,e),C(m),d(m),M(m),y(m))}}function ut(t,e,n){return e+7*t-(n+6)%7}const it={[b]:t=>t.getFullYear(),[x]:t=>Math.floor(t.getMonth()/3),[H]:t=>t.getMonth(),[j]:t=>t.getDate(),[I]:t=>t.getHours(),[B]:t=>t.getMinutes(),[E]:t=>t.getSeconds(),[L]:t=>t.getMilliseconds(),[q]:t=>P(t),[S]:t=>R(t),[S+k]:(t,e)=>ut(R(t),t.getDay(),V(e)),[k]:(t,e)=>ut(1,t.getDay(),V(e))},ct={[x]:t=>3*t,[S]:(t,e)=>ut(t,0,V(e))};function st(t,e){return ot(t,e||1,it,ct,X)}const at={[b]:t=>t.getUTCFullYear(),[x]:t=>Math.floor(t.getUTCMonth()/3),[H]:t=>t.getUTCMonth(),[j]:t=>t.getUTCDate(),[I]:t=>t.getUTCHours(),[B]:t=>t.getUTCMinutes(),[E]:t=>t.getUTCSeconds(),[L]:t=>t.getUTCMilliseconds(),[q]:t=>tt(t),[S]:t=>et(t),[k]:(t,e)=>ut(1,t.getUTCDay(),nt(e)),[S+k]:(t,e)=>ut(et(t),t.getUTCDay(),nt(e))},lt={[x]:t=>3*t,[S]:(t,e)=>ut(t,0,nt(e))};function ft(t,e){return ot(t,e||1,at,lt,rt)}const gt={[b]:l,[x]:f.every(3),[H]:f,[S]:g,[j]:m,[k]:m,[q]:m,[I]:D,[B]:T,[E]:U,[L]:h},mt={[b]:C,[x]:d.every(3),[H]:d,[S]:M,[j]:y,[k]:y,[q]:y,[I]:Y,[B]:w,[E]:p,[L]:F};function Dt(t){return gt[t]}function Tt(t){return mt[t]}function Ut(t,e,n){return t?t.offset(e,n):void 0}function ht(t,e,n){return Ut(Dt(t),e,n)}function Ct(t,e,n){return Ut(Tt(t),e,n)}function dt(t,e,n,r){return t?t.range(e,n,r):void 0}function Mt(t,e,n,r){return dt(Dt(t),e,n,r)}function yt(t,e,n,r){return dt(Tt(t),e,n,r)}const Yt=1e3,wt=6e4,pt=36e5,Ft=864e5,$t=2592e6,vt=31536e6,bt=[b,H,j,I,B,E,L],xt=bt.slice(0,-1),Ht=xt.slice(0,-1),St=Ht.slice(0,-1),jt=St.slice(0,-1),kt=[b,H],qt=[b],It=[[xt,1,Yt],[xt,5,5e3],[xt,15,15e3],[xt,30,3e4],[Ht,1,wt],[Ht,5,3e5],[Ht,15,9e5],[Ht,30,18e5],[St,1,pt],[St,3,108e5],[St,6,216e5],[St,12,432e5],[jt,1,Ft],[[b,S],1,6048e5],[kt,1,$t],[kt,3,7776e6],[qt,1,vt]];function Bt(t){const e=t.extent,n=t.maxbins||40,r=Math.abs(o(e))/n;let u,i,c=$((t=>t[2])).right(It,r);return c===It.length?(u=qt,i=v(e[0]/vt,e[1]/vt,n)):c?(c=It[r/It[c-1][2]<It[c][2]/r?c-1:c],u=c[0],i=c[1]):(u=bt,i=Math.max(v(e[0],e[1],n),1)),{units:u,step:i}}export{j as DATE,k as DAY,q as DAYOFYEAR,I as HOURS,L as MILLISECONDS,B as MINUTES,H as MONTH,x as QUARTER,E as SECONDS,Q as TIME_UNITS,S as WEEK,b as YEAR,N as dayofyear,Bt as timeBin,st as timeFloor,Dt as timeInterval,ht as timeOffset,Mt as timeSequence,G as timeUnitSpecifier,z as timeUnits,ft as utcFloor,Tt as utcInterval,Ct as utcOffset,yt as utcSequence,Z as utcdayofyear,_ as utcweek,O as week};export default null;
