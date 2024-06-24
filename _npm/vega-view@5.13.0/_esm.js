/**
 * Bundled by jsDelivr using Rollup v2.79.1 and Terser v5.19.2.
 * Original file: /npm/vega-view@5.13.0/build/vega-view.module.js
 *
 * Do NOT use SRI with dynamically generated files! More information: https://www.jsdelivr.com/using-sri-with-dynamic-files
 */
import{inherits as e,error as t,hasOwnProperty as n,truthy as r,isObject as i,isArray as s,extend as a,stringValue as o,isString as l,array as u,debounce as c,isDate as d,constant as h,toSet as g}from"../vega-util@1.17.2/_esm.js";import{Dataflow as p,asyncCallback as f,changeset as v,isChangeSet as m,EventStream as _,transforms as w}from"../vega-dataflow@5.7.6/_esm.js";import{renderModule as b,CanvasHandler as y,RenderType as z,Scenegraph as k,point as C}from"../vega-scenegraph@4.13.0/_esm.js";import{tickStep as L}from"../d3-array@3.2.4/_esm.js";import{functionContext as x}from"../vega-functions@5.15.0/_esm.js";import{context as E}from"../vega-runtime@6.2.0/_esm.js";import{interval as A}from"../d3-timer@3.0.1/_esm.js";import{locale as R}from"../vega-format@1.1.2/_esm.js";function S(e,t){e&&(null==t?e.removeAttribute("aria-label"):e.setAttribute("aria-label",t))}const D="default";function U(e,t){const n=e.globalCursor()?"undefined"!=typeof document&&document.body:e.container();if(n)return null==t?n.style.removeProperty("cursor"):n.style.cursor=t}function W(e,r){var i=e._runtime.data;return n(i,r)||t("Unrecognized data set: "+r),i[r]}function H(e,n){m(n)||t("Second argument to changes must be a changeset.");const r=W(this,e);return r.modified=!0,this.pulse(r.input,n)}function P(e){var t=e.padding();return Math.max(0,e._viewWidth+t.left+t.right)}function T(e){var t=e.padding();return Math.max(0,e._viewHeight+t.top+t.bottom)}function M(e){var t=e.padding(),n=e._origin;return[t.left+n[0],t.top+n[1]]}function j(e,t,n){var r,i,s,a=e._renderer,o=a&&a.canvas();return o&&(s=M(e),i=t.changedTouches?t.changedTouches[0]:t,(r=C(i,o))[0]-=s[0],r[1]-=s[1]),t.dataflow=e,t.item=n,t.vega=function(e,t,n){const r=t?"group"===t.mark.marktype?t:t.mark.group:null;function i(e){var n,i=r;if(e)for(n=t;n;n=n.mark.group)if(n.mark.name===e){i=n;break}return i&&i.mark&&i.mark.interactive?i:{}}function s(e){if(!e)return n;l(e)&&(e=i(e));const t=n.slice();for(;e;)t[0]-=e.x||0,t[1]-=e.y||0,e=e.mark&&e.mark.group;return t}return{view:h(e),item:h(t||{}),group:i,xy:s,x:e=>s(e)[0],y:e=>s(e)[1]}}(e,n,r),t}const B="view",G={trap:!1};function V(e,t,n,r){e._eventListeners.push({type:n,sources:u(t),handler:r})}function O(e,t,n){const r=e._eventConfig&&e._eventConfig[t];return!(!1===r||i(r)&&!r[n])||(e.warn(`Blocked ${t} ${n} event listener.`),!1)}function I(e){return e.item}function $(e){return e.item.mark.source}function q(e){return function(t,n){return n.vega.view().changeset().encode(n.item,e)}}function N(e,t,n){const r=document.createElement(e);for(const e in t)r.setAttribute(e,t[e]);return null!=n&&(r.textContent=n),r}const F="vega-bind",J="vega-bind-name",K="vega-bind-radio";function Q(e,t,n,r){const i=n.event||"input",s=()=>e.update(t.value);r.signal(n.signal,t.value),t.addEventListener(i,s),V(r,t,i,s),e.set=e=>{t.value=e,t.dispatchEvent(function(e){return"undefined"!=typeof Event?new Event(e):{type:e}}(i))}}function X(e,t,n,r){const i=r.signal(n.signal),s=N("div",{class:F}),a="radio"===n.input?s:s.appendChild(N("label"));a.appendChild(N("span",{class:J},n.name||n.signal)),t.appendChild(s);let o=Y;switch(n.input){case"checkbox":o=Z;break;case"select":o=ee;break;case"radio":o=te;break;case"range":o=ne}o(e,a,n,i)}function Y(e,t,n,r){const i=N("input");for(const e in n)"signal"!==e&&"element"!==e&&i.setAttribute("input"===e?"type":e,n[e]);i.setAttribute("name",n.signal),i.value=r,t.appendChild(i),i.addEventListener("input",(()=>e.update(i.value))),e.elements=[i],e.set=e=>i.value=e}function Z(e,t,n,r){const i={type:"checkbox",name:n.signal};r&&(i.checked=!0);const s=N("input",i);t.appendChild(s),s.addEventListener("change",(()=>e.update(s.checked))),e.elements=[s],e.set=e=>s.checked=!!e||null}function ee(e,t,n,r){const i=N("select",{name:n.signal}),s=n.labels||[];n.options.forEach(((e,t)=>{const n={value:e};re(e,r)&&(n.selected=!0),i.appendChild(N("option",n,(s[t]||e)+""))})),t.appendChild(i),i.addEventListener("change",(()=>{e.update(n.options[i.selectedIndex])})),e.elements=[i],e.set=e=>{for(let t=0,r=n.options.length;t<r;++t)if(re(n.options[t],e))return void(i.selectedIndex=t)}}function te(e,t,n,r){const i=N("span",{class:K}),s=n.labels||[];t.appendChild(i),e.elements=n.options.map(((t,a)=>{const o={type:"radio",name:n.signal,value:t};re(t,r)&&(o.checked=!0);const l=N("input",o);l.addEventListener("change",(()=>e.update(t)));const u=N("label",{},(s[a]||t)+"");return u.prepend(l),i.appendChild(u),l})),e.set=t=>{const n=e.elements,r=n.length;for(let e=0;e<r;++e)re(n[e].value,t)&&(n[e].checked=!0)}}function ne(e,t,n,r){r=void 0!==r?r:(+n.max+ +n.min)/2;const i=null!=n.max?n.max:Math.max(100,+r)||100,s=n.min||Math.min(0,i,+r)||0,a=n.step||L(s,i,100),o=N("input",{type:"range",name:n.signal,min:s,max:i,step:a});o.value=r;const l=N("span",{},+r);t.appendChild(o),t.appendChild(l);const u=()=>{l.textContent=o.value,e.update(+o.value)};o.addEventListener("input",u),o.addEventListener("change",u),e.elements=[o],e.set=e=>{o.value=e,l.textContent=e}}function re(e,t){return e===t||e+""==t+""}function ie(e,t,n,r,i,s){return(t=t||new r(e.loader())).initialize(n,P(e),T(e),M(e),i,s).background(e.background())}function se(e,t){return t?function(){try{t.apply(this,arguments)}catch(t){e.error(t)}}:null}function ae(e,t,n){if("string"==typeof t){if("undefined"==typeof document)return e.error("DOM document instance not found."),null;if(!(t=document.querySelector(t)))return e.error("Signal bind element not found: "+t),null}if(t&&n)try{t.textContent=""}catch(n){t=null,e.error(n)}return t}const oe=e=>+e||0;function le(e){return i(e)?{top:oe(e.top),bottom:oe(e.bottom),left:oe(e.left),right:oe(e.right)}:(e=>({top:e,bottom:e,left:e,right:e}))(oe(e))}async function ue(e,n,r,i){const s=b(n),a=s&&s.headless;return a||t("Unrecognized renderer type: "+n),await e.runAsync(),ie(e,null,null,a,r,i).renderAsync(e._scenegraph.root)}var ce="width",de="height",he="padding",ge={skip:!0};function pe(e,t){var n=e.autosize(),r=e.padding();return t-(n&&n.contains===he?r.left+r.right:0)}function fe(e,t){var n=e.autosize(),r=e.padding();return t-(n&&n.contains===he?r.top+r.bottom:0)}function ve(e,t){return t.modified&&s(t.input.value)&&!e.startsWith("_:vega:_")}function me(e,t){return!("parent"===e||t instanceof w.proxy)}function _e(e,t,n,r){const a=e.element();a&&a.setAttribute("title",function(e){return null==e?"":s(e)?we(e):i(e)&&!d(e)?(t=e,Object.keys(t).map((e=>{const n=t[e];return e+": "+(s(n)?we(n):be(n))})).join("\n")):e+"";var t}(r))}function we(e){return"["+e.map(be).join(", ")+"]"}function be(e){return s(e)?"[…]":i(e)&&!d(e)?"{…}":e}function ye(e,t){const n=this;if(t=t||{},p.call(n),t.loader&&n.loader(t.loader),t.logger&&n.logger(t.logger),null!=t.logLevel&&n.logLevel(t.logLevel),t.locale||e.locale){const r=a({},e.locale,t.locale);n.locale(R(r.number,r.time))}n._el=null,n._elBind=null,n._renderType=t.renderer||z.Canvas,n._scenegraph=new k;const r=n._scenegraph.root;n._renderer=null,n._tooltip=t.tooltip||_e,n._redraw=!0,n._handler=(new y).scene(r),n._globalCursor=!1,n._preventDefault=!1,n._timers=[],n._eventListeners=[],n._resizeListeners=[],n._eventConfig=function(e){const t=a({defaults:{}},e),n=(e,t)=>{t.forEach((t=>{s(e[t])&&(e[t]=g(e[t]))}))};return n(t.defaults,["prevent","allow"]),n(t,["view","window","selector"]),t}(e.eventConfig),n.globalCursor(n._eventConfig.globalCursor);const i=function(e,t,n){return E(e,w,x,n).parse(t)}(n,e,t.expr);n._runtime=i,n._signals=i.signals,n._bind=(e.bindings||[]).map((e=>({state:null,param:a({},e)}))),i.root&&i.root.set(r),r.source=i.data.root.input,n.pulse(i.data.root.input,n.changeset().insert(r.items)),n._width=n.width(),n._height=n.height(),n._viewWidth=pe(n,n._width),n._viewHeight=fe(n,n._height),n._origin=[0,0],n._resize=0,n._autosize=1,function(e){var t=e._signals,n=t[ce],r=t[de],i=t[he];function s(){e._autosize=e._resize=1}e._resizeWidth=e.add(null,(t=>{e._width=t.size,e._viewWidth=pe(e,t.size),s()}),{size:n}),e._resizeHeight=e.add(null,(t=>{e._height=t.size,e._viewHeight=fe(e,t.size),s()}),{size:r});const a=e.add(null,s,{pad:i});e._resizeWidth.rank=n.rank+1,e._resizeHeight.rank=r.rank+1,a.rank=i.rank+1}(n),function(e){e.add(null,(t=>(e._background=t.bg,e._resize=1,t.bg)),{bg:e._signals.background})}(n),function(e){const t=e._signals.cursor||(e._signals.cursor=e.add({user:D,item:null}));e.on(e.events("view","pointermove"),t,((e,n)=>{const r=t.value,i=r?l(r)?r:r.user:D,s=n.item&&n.item.cursor||null;return r&&i===r.user&&s==r.item?r:{user:i,item:s}})),e.add(null,(function(t){let n=t.cursor,r=this.value;return l(n)||(r=n.item,n=n.user),U(e,n&&n!==D?n:r||n),r}),{cursor:t})}(n),n.description(e.description),t.hover&&n.hover(),t.container&&n.initialize(t.container,t.bind),t.watchPixelRatio&&n._watchPixelRatio()}function ze(e,r){return n(e._signals,r)?e._signals[r]:t("Unrecognized signal name: "+o(r))}function ke(e,t){const n=(e._targets||[]).filter((e=>e._update&&e._update.handler===t));return n.length?n[0]:null}function Ce(e,t,n,r){let i=ke(n,r);return i||(i=se(e,(()=>r(t,n.value))),i.handler=r,e.on(n,null,i)),e}function Le(e,t,n){const r=ke(t,n);return r&&t._targets.remove(r),e}e(ye,p,{async evaluate(e,t,n){if(await p.prototype.evaluate.call(this,e,t),this._redraw||this._resize)try{this._renderer&&(this._resize&&(this._resize=0,i=M(r=this),s=P(r),a=T(r),r._renderer.background(r.background()),r._renderer.resize(s,a,i),r._handler.origin(i),r._resizeListeners.forEach((e=>{try{e(s,a)}catch(e){r.error(e)}}))),await this._renderer.renderAsync(this._scenegraph.root)),this._redraw=!1}catch(e){this.error(e)}var r,i,s,a;return n&&f(this,n),this},dirty(e){this._redraw=!0,this._renderer&&this._renderer.dirty(e)},description(e){if(arguments.length){const t=null!=e?e+"":null;return t!==this._desc&&S(this._el,this._desc=t),this}return this._desc},container(){return this._el},scenegraph(){return this._scenegraph},origin(){return this._origin.slice()},signal(e,t,n){const r=ze(this,e);return 1===arguments.length?r.value:this.update(r,t,n)},width(e){return arguments.length?this.signal("width",e):this.signal("width")},height(e){return arguments.length?this.signal("height",e):this.signal("height")},padding(e){return arguments.length?this.signal("padding",le(e)):le(this.signal("padding"))},autosize(e){return arguments.length?this.signal("autosize",e):this.signal("autosize")},background(e){return arguments.length?this.signal("background",e):this.signal("background")},renderer(e){return arguments.length?(b(e)||t("Unrecognized renderer type: "+e),e!==this._renderType&&(this._renderType=e,this._resetRenderer()),this):this._renderType},tooltip(e){return arguments.length?(e!==this._tooltip&&(this._tooltip=e,this._resetRenderer()),this):this._tooltip},loader(e){return arguments.length?(e!==this._loader&&(p.prototype.loader.call(this,e),this._resetRenderer()),this):this._loader},resize(){return this._autosize=1,this.touch(ze(this,"autosize"))},_resetRenderer(){this._renderer&&(this._renderer=null,this.initialize(this._el,this._elBind))},_resizeView:function(e,t,n,r,i,s){this.runAfter((a=>{let o=0;a._autosize=0,a.width()!==n&&(o=1,a.signal(ce,n,ge),a._resizeWidth.skip(!0)),a.height()!==r&&(o=1,a.signal(de,r,ge),a._resizeHeight.skip(!0)),a._viewWidth!==e&&(a._resize=1,a._viewWidth=e),a._viewHeight!==t&&(a._resize=1,a._viewHeight=t),a._origin[0]===i[0]&&a._origin[1]===i[1]||(a._resize=1,a._origin=i),o&&a.run("enter"),s&&a.runAfter((e=>e.resize()))}),!1,1)},addEventListener(e,t,n){let r=t;return n&&!1===n.trap||(r=se(this,t),r.raw=t),this._handler.on(e,r),this},removeEventListener(e,t){for(var n,r,i=this._handler.handlers(e),s=i.length;--s>=0;)if(r=i[s].type,n=i[s].handler,e===r&&(t===n||t===n.raw)){this._handler.off(r,n);break}return this},addResizeListener(e){const t=this._resizeListeners;return t.includes(e)||t.push(e),this},removeResizeListener(e){var t=this._resizeListeners,n=t.indexOf(e);return n>=0&&t.splice(n,1),this},addSignalListener(e,t){return Ce(this,e,ze(this,e),t)},removeSignalListener(e,t){return Le(this,ze(this,e),t)},addDataListener(e,t){return Ce(this,e,W(this,e).values,t)},removeDataListener(e,t){return Le(this,W(this,e).values,t)},globalCursor(e){if(arguments.length){if(this._globalCursor!==!!e){const t=U(this,null);this._globalCursor=!!e,t&&U(this,t)}return this}return this._globalCursor},preventDefault(e){return arguments.length?(this._preventDefault=e,this):this._preventDefault},timer:function(e,t){this._timers.push(A((function(t){e({timestamp:Date.now(),elapsed:t})}),t))},events:function(e,t,n){var r,i=this,s=new _(n),a=function(n,r){i.runAsync(null,(()=>{e===B&&function(e,t){var n=e._eventConfig.defaults,r=n.prevent,i=n.allow;return!1!==r&&!0!==i&&(!0===r||!1===i||(r?r[t]:i?!i[t]:e.preventDefault()))}(i,t)&&n.preventDefault(),s.receive(j(i,n,r))}))};if("timer"===e)O(i,"timer",t)&&i.timer(a,t);else if(e===B)O(i,"view",t)&&i.addEventListener(t,a,G);else if("window"===e?O(i,"window",t)&&"undefined"!=typeof window&&(r=[window]):"undefined"!=typeof document&&O(i,"selector",t)&&(r=Array.from(document.querySelectorAll(e))),r){for(var o=0,l=r.length;o<l;++o)r[o].addEventListener(t,a);V(i,r,t,a)}else i.warn("Can not resolve event source: "+e);return s},finalize:function(){var e,t,n,r,i,s=this._tooltip,a=this._timers,o=this._handler.handlers(),l=this._eventListeners;for(e=a.length;--e>=0;)a[e].stop();for(e=l.length;--e>=0;)for(t=(n=l[e]).sources.length;--t>=0;)n.sources[t].removeEventListener(n.type,n.handler);for(s&&s.call(this,this._handler,null,null,null),e=o.length;--e>=0;)i=o[e].type,r=o[e].handler,this._handler.off(i,r);return this},hover:function(e,t){return t=[t||"update",(e=[e||"hover"])[0]],this.on(this.events("view","pointerover",I),$,q(e)),this.on(this.events("view","pointerout",I),$,q(t)),this},data:function(e,t){return arguments.length<2?W(this,e).values.value:H.call(this,e,v().remove(r).insert(t))},change:H,insert:function(e,t){return H.call(this,e,v().insert(t))},remove:function(e,t){return H.call(this,e,v().remove(t))},scale:function(e){var r=this._runtime.scales;return n(r,e)||t("Unrecognized scale or projection: "+e),r[e].value},initialize:function(e,t){const n=this,r=n._renderType,i=n._eventConfig.bind,s=b(r);e=n._el=e?ae(n,e,!0):null,function(e){const t=e.container();t&&(t.setAttribute("role","graphics-document"),t.setAttribute("aria-roleDescription","visualization"),S(t,e.description()))}(n),s||n.error("Unrecognized renderer type: "+r);const a=s.handler||y,o=e?s.renderer:s.headless;return n._renderer=o?ie(n,n._renderer,e,o):null,n._handler=function(e,t,n,r){const i=new r(e.loader(),se(e,e.tooltip())).scene(e.scenegraph().root).initialize(n,M(e),e);return t&&t.handlers().forEach((e=>{i.on(e.type,e.handler)})),i}(n,n._handler,e,a),n._redraw=!0,e&&"none"!==i&&(t=t?n._elBind=ae(n,t,!0):e.appendChild(N("form",{class:"vega-bindings"})),n._bind.forEach((e=>{e.param.element&&"container"!==i&&(e.element=ae(n,e.param.element,!!e.param.input))})),n._bind.forEach((e=>{!function(e,t,n){if(!t)return;const r=n.param;let i=n.state;i||(i=n.state={elements:null,active:!1,set:null,update:t=>{t!=e.signal(r.signal)&&e.runAsync(null,(()=>{i.source=!0,e.signal(r.signal,t)}))}},r.debounce&&(i.update=c(r.debounce,i.update))),(null==r.input&&r.element?Q:X)(i,t,r,e),i.active||(e.on(e._signals[r.signal],null,(()=>{i.source?i.source=!1:i.set(e.signal(r.signal))})),i.active=!0)}(n,e.element||t,e)}))),n},toImageURL:async function(e,n){e!==z.Canvas&&e!==z.SVG&&e!==z.PNG&&t("Unrecognized image type: "+e);const r=await ue(this,e,n);return e===z.SVG?function(e,t){const n=new Blob([e],{type:t});return window.URL.createObjectURL(n)}(r.svg(),"image/svg+xml"):r.canvas().toDataURL("image/png")},toCanvas:async function(e,t){return(await ue(this,z.Canvas,e,t)).canvas()},toSVG:async function(e){return(await ue(this,z.SVG,e)).svg()},getState:function(e){return this._runtime.getState(e||{data:ve,signals:me,recurse:!0})},setState:function(e){return this.runAsync(null,(t=>{t._trigger=!1,t._runtime.setState(e)}),(e=>{e._trigger=!0})),this},_watchPixelRatio:function(){if("canvas"===this.renderer()&&this._renderer._canvas){let e=null;const t=()=>{null!=e&&e();const n=matchMedia(`(resolution: ${window.devicePixelRatio}dppx)`);n.addEventListener("change",t),e=()=>{n.removeEventListener("change",t)},this._renderer._canvas.getContext("2d").pixelRatio=window.devicePixelRatio||1,this._redraw=!0,this._resize=1,this.resize().runAsync()};t()}}});export{ye as View};export default null;
