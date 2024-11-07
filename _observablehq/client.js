var ne=Object.defineProperty;var r=(e,t)=>ne(e,"name",{value:t,configurable:!0});import{Inspector as E,Runtime as se}from"./runtime.js";import{Generators as y,resize as ae,FileAttachment as ie,Mutable as le}from"./stdlib.js";var ce=Object.defineProperty,B=r((e,t)=>ce(e,"name",{value:t,configurable:!0}),"o$3");const N=document.createElement("template");N.innerHTML='<button title="Copy code" class="observablehq-pre-copy"><svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 6C2 5.44772 2.44772 5 3 5H10C10.5523 5 11 5.44772 11 6V13C11 13.5523 10.5523 14 10 14H3C2.44772 14 2 13.5523 2 13V6Z M4 2.00004L12 2.00001C13.1046 2 14 2.89544 14 4.00001V12"></path></svg></button>',D();function D(){for(const e of document.querySelectorAll("pre:not([data-copy=none])")){const t=e.parentNode;if(t.classList.contains("observablehq-pre-container"))continue;const o=t.insertBefore(document.createElement("div"),e);o.className="observablehq-pre-container",Object.assign(o.dataset,e.dataset),o.appendChild(N.content.cloneNode(!0).firstChild).addEventListener("click",O),o.appendChild(e)}}r(D,"r$1"),B(D,"enableCopyButtons");async function O({currentTarget:e}){await navigator.clipboard.writeText(e.nextElementSibling.textContent.trim());const[t]=e.getAnimations({subtree:!0});t&&(t.currentTime=0),e.classList.add("observablehq-pre-copied"),e.addEventListener("animationend",()=>e.classList.remove("observablehq-pre-copied"),{once:!0})}r(O,"c$3"),B(O,"copy");var de=Object.defineProperty,A=r((e,t)=>de(e,"name",{value:t,configurable:!0}),"s$3");const m=document.querySelector("#observablehq-sidebar-toggle");if(m){let e=m.indeterminate;m.onclick=()=>{const o=matchMedia("(min-width: calc(640px + 6rem + 272px))").matches;e?(m.checked=!o,e=!1):m.checked===o&&(e=!0),m.indeterminate=e,e?sessionStorage.removeItem("observablehq-sidebar"):sessionStorage.setItem("observablehq-sidebar",m.checked)},addEventListener("keypress",o=>{o.code==="KeyB"&&(o.metaKey||o.altKey)&&!o.ctrlKey&&(o.target===document.body||o.target===m||o.target?.closest("#observablehq-sidebar"))&&(m.click(),o.preventDefault())});const t=`Toggle sidebar ${/Mac|iPhone/.test(navigator.platform)?/Firefox/.test(navigator.userAgent)?"\u2325":"\u2318":"Alt-"}B`;for(const o of document.querySelectorAll("#observablehq-sidebar-toggle, label[for='observablehq-sidebar-toggle']"))o.title=t}function R(e){e.detail>1&&e.preventDefault()}r(R,"l$4"),A(R,"preventDoubleClick");function I(){sessionStorage.setItem(`observablehq-sidebar:${this.firstElementChild.textContent}`,this.open)}r(I,"i$3"),A(I,"persistOpen");for(const e of document.querySelectorAll("#observablehq-sidebar summary"))e.onmousedown=R,e.parentElement.ontoggle=I;var pe=Object.defineProperty,P=r((e,t)=>pe(e,"name",{value:t,configurable:!0}),"l$3");const _=document.querySelector("#observablehq-toc");if(_){const e=_.appendChild(document.createElement("div"));e.classList.add("observablehq-secondary-link-highlight");const t=document.querySelector("#observablehq-main"),o=Array.from(t.querySelectorAll(_.dataset.selector)).reverse(),s=_.querySelectorAll(".observablehq-secondary-link"),q=P(()=>{for(const a of s)a.classList.remove("observablehq-secondary-link-active");if(location.hash)for(const a of o){const u=encodeURI(`#${a.id}`);if(u===location.hash){const f=a.getBoundingClientRect().top;if(0<f&&f<40){for(const g of s)if(g.querySelector("a[href]")?.hash===u)return g.classList.add("observablehq-secondary-link-active"),g;return}break}}for(const a of o){if(a.getBoundingClientRect().top>=innerHeight*.5)continue;const u=a.querySelector("a[href]")?.hash;for(const f of s)if(f.querySelector("a[href]")?.hash===u)return f.classList.add("observablehq-secondary-link-active"),f;break}},"relink"),C=P(()=>{const a=q();e.style.cssText=a?`top: ${a.offsetTop}px; height: ${a.offsetHeight}px;`:""},"intersected"),v=new IntersectionObserver(C,{rootMargin:"0px 0px -50% 0px"});for(const a of o)v.observe(a)}var me=Object.defineProperty,T=r((e,t)=>me(e,"name",{value:t,configurable:!0}),"n$1");function M(e){const t=new E(document.createElement("div"));return t.fulfilled(e),t._node.firstChild}r(M,"i$2"),T(M,"inspect");function z(e){const t=new E(document.createElement("div"));t.rejected(e);const o=t._node.firstChild;return o.classList.add("observablehq--error"),o}r(z,"s$1"),T(z,"inspectError");var ue=Object.defineProperty,n=r((e,t)=>ue(e,"name",{value:t,configurable:!0}),"o$1");const fe=n(()=>import("../_npm/lodash@4.17.21/_esm.js").then(e=>e.default),"_"),be=n(()=>import("../_npm/arquero@7.2.0/_esm.js"),"aq"),he=n(()=>import("../_npm/apache-arrow@18.0.0/_esm.js"),"Arrow"),ve=n(()=>import("../_npm/d3@7.9.0/_esm.js"),"d3"),ge=n(()=>import("./stdlib/dot.js").then(e=>e.default),"dot"),ye=n(()=>import("../_npm/@duckdb/duckdb-wasm@1.28.0/_esm.js"),"duckdb"),$e=n(()=>import("./stdlib/duckdb.js").then(e=>e.DuckDBClient),"DuckDBClient"),qe=n(()=>import("../_npm/echarts@5.5.1/dist/echarts.esm.min.js._esm.js"),"echarts"),we=n(()=>import("../_npm/htl@0.3.1/_esm.js"),"htl"),_e=n(()=>import("../_npm/htl@0.3.1/_esm.js").then(e=>e.html),"html"),ke=n(()=>import("../_npm/htl@0.3.1/_esm.js").then(e=>e.svg),"svg"),xe=n(()=>import("./stdlib/inputs.js"),"Inputs"),Ce=n(()=>import("../_npm/leaflet@1.9.4/_esm.js"),"L"),Le=n(()=>import("../_npm/mapbox-gl@3.7.0/_esm.js").then(e=>e.default),"mapboxgl"),Se=n(()=>import("./stdlib/mermaid.js").then(e=>e.default),"mermaid"),je=n(()=>import("../_npm/@observablehq/plot@0.6.16/_esm.js"),"Plot"),Ee=n(()=>import("../_npm/react@18.3.1/_esm.js"),"React"),Be=n(()=>import("../_npm/react-dom@18.3.1/_esm.js"),"ReactDOM"),Ne=n(()=>import("./stdlib/duckdb.js").then(e=>e.sql),"sql"),De=n(()=>import("./stdlib/sqlite.js").then(e=>e.default),"SQLite"),Oe=n(()=>import("./stdlib/sqlite.js").then(e=>e.SQLiteDatabaseClient),"SQLiteDatabaseClient"),Ae=n(()=>import("./stdlib/tex.js").then(e=>e.default),"tex"),Re=n(()=>import("../_npm/topojson-client@3.1.0/_esm.js"),"topojson"),Ie=n(()=>import("./stdlib/vgplot.js").then(e=>e.default()),"vg"),Pe=n(()=>import("./stdlib/vega-lite.js").then(e=>e.default),"vl");var Te=Object.freeze({__proto__:null,Arrow:he,DuckDBClient:$e,Inputs:xe,L:Ce,Plot:je,React:Ee,ReactDOM:Be,SQLite:De,SQLiteDatabaseClient:Oe,_:fe,aq:be,d3:ve,dot:ge,duckdb:ye,echarts:qe,htl:we,html:_e,mapboxgl:Le,mermaid:Se,sql:Ne,svg:ke,tex:Ae,topojson:Re,vg:Ie,vl:Pe}),Me=Object.defineProperty,l=r((e,t)=>Me(e,"name",{value:t,configurable:!0}),"e");const ze=l(()=>c(import.meta.resolve("../_npm/@observablehq/sample-datasets@1.0.1/aapl.csv"),!0),"aapl"),Qe=l(()=>c(import.meta.resolve("../_npm/@observablehq/sample-datasets@1.0.1/alphabet.csv"),!0),"alphabet"),He=l(()=>c(import.meta.resolve("../_npm/@observablehq/sample-datasets@1.0.1/cars.csv"),!0),"cars"),Ve=l(()=>c(import.meta.resolve("../_npm/@observablehq/sample-datasets@1.0.1/citywages.csv"),!0),"citywages"),Ke=l(()=>c(import.meta.resolve("../_npm/@observablehq/sample-datasets@1.0.1/diamonds.csv"),!0),"diamonds"),Fe=l(()=>c(import.meta.resolve("../_npm/@observablehq/sample-datasets@1.0.1/flare.csv"),!0),"flare"),Ge=l(()=>c(import.meta.resolve("../_npm/@observablehq/sample-datasets@1.0.1/industries.csv"),!0),"industries"),Je=l(()=>Q(import.meta.resolve("../_npm/@observablehq/sample-datasets@1.0.1/miserables.json")),"miserables"),Ue=l(()=>c(import.meta.resolve("../_npm/@observablehq/sample-datasets@1.0.1/olympians.csv"),!0),"olympians"),We=l(()=>c(import.meta.resolve("../_npm/@observablehq/sample-datasets@1.0.1/penguins.csv"),!0),"penguins"),Ze=l(()=>c(import.meta.resolve("../_npm/@observablehq/sample-datasets@1.0.1/pizza.csv"),!0),"pizza"),Xe=l(()=>c(import.meta.resolve("../_npm/@observablehq/sample-datasets@1.0.1/weather.csv"),!0),"weather");async function Q(e){const t=await fetch(e);if(!t.ok)throw new Error(`unable to fetch ${e}: status ${t.status}`);return t.json()}r(Q,"w"),l(Q,"json");async function H(e){const t=await fetch(e);if(!t.ok)throw new Error(`unable to fetch ${e}: status ${t.status}`);return t.text()}r(H,"y"),l(H,"text");async function c(e,t){const[o,s]=await Promise.all([H(e),import("../_npm/d3-dsv@3.0.1/_esm.js")]);return s.csvParse(o,t&&s.autoType)}r(c,"t"),l(c,"csv");var Ye=Object.freeze({__proto__:null,aapl:ze,alphabet:Qe,cars:He,citywages:Ve,diamonds:Ke,flare:Fe,industries:Ge,miserables:Je,olympians:Ue,penguins:We,pizza:Ze,weather:Xe}),et=Object.defineProperty,i=r((e,t)=>et(e,"name",{value:t,configurable:!0}),"o");const tt={now:()=>y.now(),width:()=>y.width(document.querySelector("main")),dark:()=>y.dark(),resize:()=>ae,FileAttachment:()=>ie,Generators:()=>y,Mutable:()=>le,...Te,...Ye},ot=new se(tt),V=ot.module(),j=new Map,k=X(document.body);function K(e){const{id:t,mode:o,inputs:s=[],outputs:q=[],body:C}=e,v=[];j.set(t,{cell:e,variables:v});const a=k.get(t),u=te(a);a._nodes=[],u&&a._nodes.push(u);const f=i(()=>G(a,u),"pending"),g=i(b=>J(a,b),"rejected"),p=V.variable({_node:a.parentNode,pending:f,rejected:g},{shadow:{}});if(s.includes("display")||s.includes("view")){let b=-1;const L=o==="jsx"?F:$,oe=o==="inline"?W:o==="jsx"?U:Z,S=new p.constructor(2,p._module);if(S.define(s.filter(d=>d!=="display"&&d!=="view"),()=>{let d=p._version;return w=>{if(d<b)throw new Error("stale display");return d>b&&L(a),b=d,oe(a,w),w}}),p._shadow.set("display",S),s.includes("view")){const d=new p.constructor(2,p._module,null,{shadow:{}});d._shadow.set("display",S),d.define(["display"],w=>re=>y.input(w(re))),p._shadow.set("view",d)}}p.define(q.length?`cell ${t}`:null,s,C),v.push(p);for(const b of q)v.push(V.variable(!0).define(b,[`cell ${t}`],L=>L[b]))}r(K,"F"),i(K,"define");function F(){}r(F,"O"),i(F,"noop");function $(e){for(const t of e._nodes)t.remove();e._nodes.length=0}r($,"p"),i($,"clear");function G(e,t){e._error&&(e._error=!1,$(e),t&&h(e,t))}r(G,"q"),i(G,"reset");function J(e,t){console.error(t),e._error=!0,$(e),h(e,z(t))}r(J,"C"),i(J,"reject");function U(e,t){return(e._root??=import("../_npm/react-dom@18.3.1/client._esm.js").then(({createRoot:o})=>{const s=document.createElement("DIV");return[s,o(s)]})).then(([o,s])=>{o.parentNode||(e._nodes.push(o),e.parentNode.insertBefore(o,e)),s.render(t)})}r(U,"H"),i(U,"displayJsx");function h(e,t){if(t.nodeType===11){let o;for(;o=t.firstChild;)e._nodes.push(o),e.parentNode.insertBefore(o,e)}else e._nodes.push(t),e.parentNode.insertBefore(t,e)}r(h,"l"),i(h,"displayNode");function W(e,t){if(x(t))h(e,t);else if(typeof t=="string"||!t?.[Symbol.iterator])h(e,document.createTextNode(t));else for(const o of t)h(e,x(o)?o:document.createTextNode(o))}r(W,"J"),i(W,"displayInline");function Z(e,t){h(e,x(t)?t:M(t))}r(Z,"Q"),i(Z,"displayBlock");function rt(e){$(k.get(e)),j.get(e).variables.forEach(t=>t.delete()),j.delete(e)}r(rt,"K"),i(rt,"undefine");function x(e){return e instanceof Node&&e instanceof e.constructor}r(x,"b"),i(x,"isNode");function X(e){const t=new Map,o=document.createNodeIterator(e,128,null);let s;for(;s=o.nextNode();)Y(s)&&t.set(s.data.slice(1,-1),s);return t}r(X,"B"),i(X,"findRoots");function Y(e){return e.nodeType===8&&/^:[0-9a-f]{8}(?:-\d+)?:$/.test(e.data)}r(Y,"P"),i(Y,"isRoot");function ee(e){return e.nodeType===1&&e.tagName==="OBSERVABLEHQ-LOADING"}r(ee,"U"),i(ee,"isLoading");function te(e){const t=e.previousSibling;return t&&ee(t)?t:null}r(te,"x"),i(te,"findLoading");function nt(e,t){t==null?k.delete(e):k.set(e,t)}r(nt,"W"),i(nt,"registerRoot");export{K as define};
