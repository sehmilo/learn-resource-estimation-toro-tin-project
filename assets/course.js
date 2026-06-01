/* ============================================================
   Toro Resource Estimation Course - interactive engine
   ============================================================ */
"use strict";

/* ---------- shared colours ---------- */
var C = {navy:"#1f2a44", bronze:"#c8702d", teal:"#2a7d8c",
         ink:"#26303f", line:"#ddd6c8", muted:"#6a6f78", grid:"#e4ddcf"};

/* ---------- small DOM helpers ---------- */
function el(tag, cls, txt){
  var e=document.createElement(tag);
  if(cls) e.className=cls;
  if(txt!=null) e.textContent=txt;
  return e;
}
function mkSlider(parent, key, label, min, max, step, val, fmt, oninput){
  var c=el("div","ctrl");
  var l=el("label"); var name=el("span",null,label);
  var v=el("span","val"); v.textContent=fmt(val);
  l.appendChild(name); l.appendChild(v);
  var inp=document.createElement("input");
  inp.type="range"; inp.min=min; inp.max=max; inp.step=step; inp.value=val;
  inp.addEventListener("input",function(){
    v.textContent=fmt(parseFloat(inp.value));
    oninput(parseFloat(inp.value));
  });
  c.appendChild(l); c.appendChild(inp);
  parent.appendChild(c);
  return {input:inp, setVal:function(x){inp.value=x; v.textContent=fmt(x);}};
}

/* ---------- canvas plot frame ---------- */
function Plot(canvas, xmin, xmax, ymin, ymax, pad){
  var dpr=window.devicePixelRatio||1;
  var cw=canvas.clientWidth||canvas.width, ch=canvas.height;
  canvas.width=cw*dpr; canvas.height=ch*dpr;
  canvas.style.height=ch+"px";
  var g=canvas.getContext("2d"); g.scale(dpr,dpr);
  pad=pad||{l:58,r:18,t:16,b:42};
  var W=cw, H=ch;
  function X(x){return pad.l+(x-xmin)/(xmax-xmin)*(W-pad.l-pad.r);}
  function Y(y){return H-pad.b-(y-ymin)/(ymax-ymin)*(H-pad.t-pad.b);}
  return {g:g,W:W,H:H,pad:pad,X:X,Y:Y,xmin:xmin,xmax:xmax,ymin:ymin,ymax:ymax,
    clear:function(){g.clearRect(0,0,W,H);},
    axes:function(xlab,ylab,xt,yt){
      g.strokeStyle=C.grid; g.lineWidth=1; g.fillStyle=C.muted;
      g.font="11px -apple-system,Segoe UI,sans-serif";
      var i;
      for(i=0;i<xt.length;i++){
        g.beginPath(); g.moveTo(X(xt[i]),Y(ymin)); g.lineTo(X(xt[i]),Y(ymax));
        g.stroke();
        g.textAlign="center";
        g.fillText(String(xt[i]),X(xt[i]),H-pad.b+15);
      }
      for(i=0;i<yt.length;i++){
        g.beginPath(); g.moveTo(X(xmin),Y(yt[i])); g.lineTo(X(xmax),Y(yt[i]));
        g.stroke();
        g.textAlign="right";
        g.fillText(String(yt[i]),pad.l-7,Y(yt[i])+4);
      }
      g.strokeStyle=C.ink; g.lineWidth=1.4;
      g.beginPath(); g.moveTo(X(xmin),Y(ymin)); g.lineTo(X(xmax),Y(ymin));
      g.lineTo(X(xmax),Y(ymax)); g.stroke();
      g.beginPath(); g.moveTo(X(xmin),Y(ymin)); g.lineTo(X(xmin),Y(ymax)); g.stroke();
      g.fillStyle=C.navy; g.font="bold 12px -apple-system,Segoe UI,sans-serif";
      g.textAlign="center"; g.fillText(xlab,pad.l+(W-pad.l-pad.r)/2,H-6);
      g.save(); g.translate(13,pad.t+(H-pad.t-pad.b)/2); g.rotate(-Math.PI/2);
      g.fillText(ylab,0,0); g.restore();
    },
    line:function(pts,col,w,dash){
      g.strokeStyle=col; g.lineWidth=w||2; g.setLineDash(dash||[]);
      g.beginPath();
      for(var i=0;i<pts.length;i++){
        var px=X(pts[i][0]),py=Y(pts[i][1]);
        if(i===0)g.moveTo(px,py); else g.lineTo(px,py);
      }
      g.stroke(); g.setLineDash([]);
    },
    dot:function(x,y,r,fill,stroke){
      g.beginPath(); g.arc(X(x),Y(y),r,0,6.2832);
      if(fill){g.fillStyle=fill; g.fill();}
      if(stroke){g.strokeStyle=stroke; g.lineWidth=1.5; g.stroke();}
    },
    hline:function(y,col,dash){
      g.strokeStyle=col; g.lineWidth=1.4; g.setLineDash(dash||[]);
      g.beginPath(); g.moveTo(X(xmin),Y(y)); g.lineTo(X(xmax),Y(y)); g.stroke();
      g.setLineDash([]);
    },
    vline:function(x,col,dash){
      g.strokeStyle=col; g.lineWidth=1.4; g.setLineDash(dash||[]);
      g.beginPath(); g.moveTo(X(x),Y(ymin)); g.lineTo(X(x),Y(ymax)); g.stroke();
      g.setLineDash([]);
    },
    bar:function(x0,x1,y,col){
      g.fillStyle=col;
      g.fillRect(X(x0),Y(y),X(x1)-X(x0),Y(ymin)-Y(y));
      g.strokeStyle="#fff"; g.lineWidth=1;
      g.strokeRect(X(x0),Y(y),X(x1)-X(x0),Y(ymin)-Y(y));
    },
    label:function(x,y,txt,col,align){
      g.fillStyle=col||C.ink; g.textAlign=align||"left";
      g.font="11px -apple-system,Segoe UI,sans-serif";
      g.fillText(txt,X(x),Y(y));
    }
  };
}

/* ---------- copy-code buttons ---------- */
function initCopy(){
  var heads=document.querySelectorAll(".code-head");
  heads.forEach(function(h){
    var b=el("button","copybtn","Copy"); b.style.cssText=
      "background:none;border:1px solid #3a465e;color:#8b97ad;"+
      "border-radius:5px;padding:2px 10px;cursor:pointer;font-size:11px";
    b.addEventListener("click",function(){
      var pre=h.parentElement.querySelector("code");
      navigator.clipboard.writeText(pre.innerText).then(function(){
        b.textContent="Copied"; setTimeout(function(){b.textContent="Copy";},1400);
      });
    });
    h.appendChild(b);
  });
}

/* ---------- quizzes ---------- */
function initQuiz(){
  document.querySelectorAll(".quiz").forEach(function(q){
    var opts=q.querySelectorAll(".opt");
    var exp=q.querySelector(".explain");
    opts.forEach(function(o){
      o.addEventListener("click",function(){
        opts.forEach(function(x){x.classList.remove("correct","wrong");});
        if(o.dataset.correct==="1") o.classList.add("correct");
        else{ o.classList.add("wrong");
          opts.forEach(function(x){
            if(x.dataset.correct==="1") x.classList.add("correct");});
        }
        if(exp) exp.classList.add("show");
      });
    });
  });
}

/* ============================================================
   WIDGET 1 - Variogram explorer  (Module 4)
   ============================================================ */
var VARIO = {
  h:[180,360,540,720,900,1080,1260,1440,1620],
  g:[2.192,3.157,2.394,3.304,3.898,5.046,8.795,6.114,3.278],
  n:[37,35,42,32,32,24,8,12,5],
  fit:{nugget:1.88, sill:3.44, range:1052}, variance:3.44
};
function sphModel(h,nug,sill,rng){
  if(h<=0) return 0;
  if(h>=rng) return sill;
  var r=h/rng;
  return nug+(sill-nug)*(1.5*r-0.5*r*r*r);
}
function initVariogram(){
  var host=document.getElementById("vario-widget");
  if(!host) return;
  host.appendChild(mkW("Variogram model explorer",
    "Drag the three structural parameters and watch the spherical model "+
    "chase the real Toro experimental variogram. Filled points are reliable "+
    "(>=20 pairs); hollow points are noise."));
  var cv=document.createElement("canvas");
  cv.height=380; cv.style.width="100%";
  host.appendChild(cv);
  var ctrls=el("div","controls"); host.appendChild(ctrls);
  var ro=el("div","readout"); host.appendChild(ro);
  var st={nug:0.6, sill:4.2, rng:600};
  var sN,sS,sR;
  function draw(){
    var P=Plot(cv,0,1700,0,9,{l:56,r:16,t:14,b:42});
    P.clear();
    P.axes("Lag distance h (m)","Semivariance gamma(h)",
      [0,400,800,1200,1600],[0,2,4,6,8]);
    P.hline(VARIO.variance,C.muted,[5,4]);
    P.label(1480,VARIO.variance+0.25,"sample variance",C.muted,"right");
    var i, wsse=0, wn=0;
    for(i=0;i<VARIO.h.length;i++){
      var rel=VARIO.n[i]>=20;
      var rad=3+Math.sqrt(VARIO.n[i]);
      P.dot(VARIO.h[i],VARIO.g[i],rad, rel?C.teal:"#fff",
            rel?"#fff":C.muted);
      if(rel){
        var d=sphModel(VARIO.h[i],st.nug,st.sill,st.rng)-VARIO.g[i];
        wsse+=VARIO.n[i]*d*d; wn+=VARIO.n[i];
      }
    }
    var curve=[];
    for(i=0;i<=1700;i+=20) curve.push([i,sphModel(i,st.nug,st.sill,st.rng)]);
    P.line(curve,C.bronze,3);
    P.vline(st.rng,C.navy,[4,3]);
    P.label(st.rng+8,0.5,"range",C.navy,"left");
    var rmse=Math.sqrt(wsse/wn);
    var quality = rmse<0.85?"excellent fit":rmse<1.3?"reasonable fit":
                  "poor fit - keep adjusting";
    ro.innerHTML="Weighted RMSE to reliable points: <b>"+rmse.toFixed(3)+
      "</b> &nbsp; ("+quality+")<br>nugget/sill ratio = <b>"+
      (st.nug/st.sill).toFixed(2)+"</b> &mdash; "+
      (st.nug/st.sill>0.5?"highly erratic grade, much variance is unstructured":
       st.nug/st.sill>0.25?"moderate short-scale randomness":
       "well-structured, continuous grade");
  }
  sN=mkSlider(ctrls,"nug","Nugget  C0",0,3.4,0.01,st.nug,
    function(v){return v.toFixed(2);},function(v){st.nug=v;
      if(st.nug>st.sill){st.sill=st.nug; sS.setVal(st.sill);} draw();});
  sS=mkSlider(ctrls,"sill","Sill  C0 + C",1,7,0.01,st.sill,
    function(v){return v.toFixed(2);},function(v){st.sill=Math.max(v,st.nug);
      draw();});
  sR=mkSlider(ctrls,"rng","Range  a (m)",200,1700,10,st.rng,
    function(v){return v.toFixed(0)+" m";},function(v){st.rng=v; draw();});
  var br=el("div","btn-row");
  var b1=el("button","wbtn","Snap to least-squares fit");
  b1.addEventListener("click",function(){
    st.nug=VARIO.fit.nugget; st.sill=VARIO.fit.sill; st.rng=VARIO.fit.range;
    sN.setVal(st.nug); sS.setVal(st.sill); sR.setVal(st.rng); draw();
  });
  var b2=el("button","wbtn alt","Pure nugget (no structure)");
  b2.addEventListener("click",function(){
    st.nug=VARIO.variance; st.sill=VARIO.variance; st.rng=600;
    sN.setVal(st.nug); sS.setVal(st.sill); sR.setVal(st.rng); draw();
  });
  br.appendChild(b1); br.appendChild(b2); host.appendChild(br);
  draw();
}
function mkW(title,sub){
  var d=document.createDocumentFragment();
  d.appendChild(el("div","wtitle",title));
  d.appendChild(el("div","wsub",sub));
  return d;
}

/* ============================================================
   WIDGET 2 - Top-cut / capping explorer  (Module 3)
   ============================================================ */
var SNO2_32=[0.15,0.357,0.387,0.392,0.455,0.611,0.633,0.637,0.654,0.656,
  0.908,0.928,1.304,1.323,1.406,1.451,1.549,1.637,1.658,1.669,1.822,2.277,
  2.354,3.116,3.22,3.969,4.28,4.62,5.576,6.036,7.588,8.842];
function initTopcut(){
  var host=document.getElementById("topcut-widget");
  if(!host) return;
  host.appendChild(mkW("Top-cut (grade capping) explorer",
    "Capping replaces every value above the cap with the cap itself. Watch "+
    "what a single decision does to the declared mean grade of the 32 Toro "+
    "concentrate samples."));
  var cv=document.createElement("canvas");
  cv.height=320; cv.style.width="100%"; host.appendChild(cv);
  var ctrls=el("div","controls"); host.appendChild(ctrls);
  var ro=el("div","readout"); host.appendChild(ro);
  var rawMean=0; SNO2_32.forEach(function(v){rawMean+=v;}); rawMean/=32;
  var cap=9.0;
  function draw(){
    var P=Plot(cv,0,10,0,9,{l:50,r:16,t:14,b:42});
    P.clear();
    P.axes("SnO2 (%)","Count",[0,2,4,6,8,10],[0,2,4,6,8]);
    var bins=new Array(10).fill(0);
    var capped=SNO2_32.map(function(v){return Math.min(v,cap);});
    capped.forEach(function(v){var b=Math.min(9,Math.floor(v)); bins[b]++;});
    for(var i=0;i<10;i++) if(bins[i]>0) P.bar(i+0.08,i+0.92,bins[i],C.teal);
    P.vline(cap,C.bronze,[5,4]);
    P.label(cap-0.15,8.4,"cap",C.bronze,"right");
    var capMean=0; capped.forEach(function(v){capMean+=v;}); capMean/=32;
    var nCut=SNO2_32.filter(function(v){return v>cap;}).length;
    var drop=(1-capMean/rawMean)*100;
    ro.innerHTML="Uncapped mean: <b>"+rawMean.toFixed(3)+"%</b>"+
      " &nbsp;|&nbsp; Capped mean: <b>"+capMean.toFixed(3)+"%</b>"+
      " &nbsp;|&nbsp; samples cut: <b>"+nCut+"</b><br>"+
      "Effect on declared grade: <b>"+(drop>0.05?"-"+drop.toFixed(1)+"%":
      "negligible")+"</b> &mdash; "+
      (cap<=3?"aggressive cap, you are discarding real metal":
       cap<=6?"moderate cap, defensible if the high values are erratic":
       "light or no cap");
  }
  mkSlider(ctrls,"cap","Cap value (%)",1,9,0.1,cap,
    function(v){return v.toFixed(1)+"%";},function(v){cap=v; draw();});
  draw();
}

/* ============================================================
   WIDGET 3 - Grade-tonnage / cut-off  (Module 6)
   ============================================================ */
var GT=[[0,48.756,2.419],[0.25,48.756,2.419],[0.5,48.756,2.419],
  [0.75,48.756,2.419],[1,48.756,2.419],[1.25,48.756,2.419],
  [1.5,47.586,2.444],[1.75,45.636,2.478],[2,42.497,2.521],
  [2.25,35.253,2.6],[2.5,11.553,3.066],[2.75,7.982,3.269],
  [3,5.622,3.436],[3.25,3.714,3.602],[3.5,2.216,3.763],
  [3.75,1.005,3.942],[4,0.308,4.102]];
function gtAt(c){
  if(c<=0) return GT[0];
  for(var i=1;i<GT.length;i++) if(GT[i][0]>=c){
    var a=GT[i-1],b=GT[i],f=(c-a[0])/(b[0]-a[0]);
    return [c,a[1]+f*(b[1]-a[1]),a[2]+f*(b[2]-a[2])];
  }
  return GT[GT.length-1];
}
function initGradeTonnage(){
  var host=document.getElementById("gt-widget");
  if(!host) return;
  host.appendChild(mkW("Grade-tonnage / cut-off explorer",
    "The cut-off grade is the single most powerful lever in a resource "+
    "statement. Slide it across the Toro demonstration block model and "+
    "watch tonnes trade against grade."));
  var cv=document.createElement("canvas");
  cv.height=340; cv.style.width="100%"; host.appendChild(cv);
  var ctrls=el("div","controls"); host.appendChild(ctrls);
  var ro=el("div","readout"); host.appendChild(ro);
  var cut=2.0;
  function draw(){
    var P=Plot(cv,0,4,0,55,{l:54,r:54,t:16,b:42});
    P.clear();
    P.axes("Cut-off grade SnO2 (%)","Tonnage (Mt)",
      [0,1,2,3,4],[0,10,20,30,40,50]);
    var tline=GT.map(function(r){return [r[0],r[1]];});
    P.line(tline,C.teal,3);
    var gline=GT.map(function(r){return [r[0],r[2]/4.5*55];});
    P.line(gline,C.bronze,3);
    P.vline(cut,C.navy,[4,3]);
    var v=gtAt(cut);
    P.dot(cut,v[1],5,C.teal,"#fff");
    P.dot(cut,v[2]/4.5*55,5,C.bronze,"#fff");
    P.g.fillStyle=C.bronze; P.g.textAlign="left"; P.g.font="11px sans-serif";
    P.g.fillText("grade ->",P.W-90,P.pad.t+14);
    P.g.fillStyle=C.teal;
    P.g.fillText("<- tonnage",P.pad.l+6,P.pad.t+14);
    var snO2_t=v[1]*1e6*v[2]/100;
    var sn_t=snO2_t*0.7877;
    ro.innerHTML="At cut-off <b>"+cut.toFixed(2)+"% SnO2</b> &mdash; "+
      "tonnage <b>"+v[1].toFixed(1)+" Mt</b>, mean grade <b>"+
      v[2].toFixed(2)+"% SnO2</b><br>contained SnO2 <b>"+
      Math.round(snO2_t).toLocaleString()+" t</b>, "+
      "contained Sn metal <b>"+Math.round(sn_t).toLocaleString()+" t</b>";
  }
  mkSlider(ctrls,"cut","Cut-off grade (% SnO2)",0,4,0.05,cut,
    function(v){return v.toFixed(2)+"%";},function(v){cut=v; draw();});
  draw();
}

/* ============================================================
   WIDGET 4 - 1D estimation: NN vs IDW vs Kriging  (Module 5)
   ============================================================ */
function solve(A,b){
  var n=b.length, i,j,k, M=A.map(function(r,ri){return r.concat([b[ri]]);});
  for(i=0;i<n;i++){
    var p=i; for(k=i+1;k<n;k++) if(Math.abs(M[k][i])>Math.abs(M[p][i])) p=k;
    var t=M[i]; M[i]=M[p]; M[p]=t;
    for(k=i+1;k<n;k++){
      var f=M[k][i]/M[i][i];
      for(j=i;j<=n;j++) M[k][j]-=f*M[i][j];
    }
  }
  var x=new Array(n);
  for(i=n-1;i>=0;i--){
    var s=M[i][n];
    for(j=i+1;j<n;j++) s-=M[i][j]*x[j];
    x[i]=s/M[i][i];
  }
  return x;
}
function initInterp(){
  var host=document.getElementById("interp-widget");
  if(!host) return;
  host.appendChild(mkW("Estimator comparison along a drill line",
    "Six samples on a 600 m section. Compare nearest-neighbour, inverse "+
    "distance and ordinary kriging. Note which estimators honour the data "+
    "and how the nugget destroys that exactness."));
  var cv=document.createElement("canvas");
  cv.height=340; cv.style.width="100%"; host.appendChild(cv);
  var ctrls=el("div","controls"); host.appendChild(ctrls);
  var ro=el("div","readout"); host.appendChild(ro);
  var px=[40,150,250,370,470,560], pz=[1.3,4.1,2.0,5.2,1.6,3.0];
  var st={power:2.0, nugget:0.0, range:260, show:{nn:true,idw:true,ok:true}};
  function idw1(x){
    var num=0,den=0;
    for(var i=0;i<px.length;i++){
      var d=Math.abs(x-px[i]); if(d<0.5) return pz[i];
      var w=1/Math.pow(d,st.power); num+=w*pz[i]; den+=w;
    }
    return num/den;
  }
  function sph1(h){ if(h<=0)return 0; var s=1;
    if(h>=st.range) return st.nugget+(s-st.nugget);
    var r=h/st.range; return st.nugget+(s-st.nugget)*(1.5*r-0.5*r*r*r);}
  function ok1(x){
    var n=px.length,i,j;
    var A=[]; for(i=0;i<n+1;i++)A.push(new Array(n+1).fill(0));
    for(i=0;i<n;i++){for(j=0;j<n;j++)A[i][j]=sph1(Math.abs(px[i]-px[j]));
      A[i][n]=1; A[n][i]=1;}
    var b=new Array(n+1);
    for(i=0;i<n;i++)b[i]=sph1(Math.abs(px[i]-x)); b[n]=1;
    var w=solve(A,b), e=0; for(i=0;i<n;i++)e+=w[i]*pz[i];
    return e;
  }
  function nn1(x){var bi=0,bd=1e9;
    for(var i=0;i<px.length;i++){var d=Math.abs(x-px[i]);
      if(d<bd){bd=d;bi=i;}} return pz[bi];}
  function draw(){
    var P=Plot(cv,0,600,0,6.5,{l:48,r:16,t:14,b:42});
    P.clear();
    P.axes("Distance along section (m)","SnO2 grade (%)",
      [0,150,300,450,600],[0,2,4,6]);
    var i,curve;
    if(st.show.nn){curve=[];for(i=0;i<=600;i+=3)curve.push([i,nn1(i)]);
      P.line(curve,"#9aa0aa",1.8);}
    if(st.show.idw){curve=[];for(i=0;i<=600;i+=3)curve.push([i,idw1(i)]);
      P.line(curve,C.teal,2.4);}
    if(st.show.ok){curve=[];for(i=0;i<=600;i+=3)curve.push([i,ok1(i)]);
      P.line(curve,C.bronze,2.8);}
    for(i=0;i<px.length;i++) P.dot(px[i],pz[i],6,C.navy,"#fff");
    P.g.font="11px sans-serif"; P.g.textAlign="left";
    P.g.fillStyle="#9aa0aa"; if(st.show.nn)P.g.fillText("- nearest neighbour",P.pad.l+8,P.pad.t+12);
    P.g.fillStyle=C.teal; if(st.show.idw)P.g.fillText("- IDW",P.pad.l+8,P.pad.t+26);
    P.g.fillStyle=C.bronze; if(st.show.ok)P.g.fillText("- ordinary kriging",P.pad.l+8,P.pad.t+40);
    var exact=st.nugget<0.02;
    ro.innerHTML="IDW power = <b>"+st.power.toFixed(1)+"</b> "+
      "(higher power = more local, more like nearest-neighbour).<br>"+
      "Kriging nugget = <b>"+st.nugget.toFixed(2)+"</b> &mdash; "+
      (exact?"zero nugget: kriging is an <b>exact interpolator</b>, the curve "+
       "passes through every sample":
       "non-zero nugget: kriging no longer honours the samples, it "+
       "<b>smooths through</b> them");
  }
  mkSlider(ctrls,"pow","IDW power p",0.5,6,0.1,st.power,
    function(v){return v.toFixed(1);},function(v){st.power=v;draw();});
  mkSlider(ctrls,"nug","Kriging nugget",0,1,0.01,st.nugget,
    function(v){return v.toFixed(2);},function(v){st.nugget=v;draw();});
  mkSlider(ctrls,"rng","Kriging range (m)",60,500,10,st.range,
    function(v){return v.toFixed(0)+" m";},function(v){st.range=v;draw();});
  var br=el("div","btn-row");
  [["nn","Nearest neighbour"],["idw","IDW"],["ok","Kriging"]].forEach(
   function(t){
    var b=el("button","wbtn"+(st.show[t[0]]?"":" alt"),t[1]);
    b.addEventListener("click",function(){
      st.show[t[0]]=!st.show[t[0]];
      b.className="wbtn"+(st.show[t[0]]?"":" alt"); draw();
    });
    br.appendChild(b);
  });
  host.appendChild(br);
  draw();
}

/* ============================================================
   WIDGET 5 - Resource classification by drill spacing (Module 1)
   ============================================================ */
function initClassify(){
  var host=document.getElementById("classify-widget");
  if(!host) return;
  host.appendChild(mkW("Classification and drill spacing",
    "Confidence in a Mineral Resource is governed largely by data density. "+
    "Move the drill spacing and QAQC quality and see how the category, and "+
    "the honest economic use of the resource, change."));
  var ctrls=el("div","controls"); host.appendChild(ctrls);
  var box=el("div"); box.style.cssText=
    "border-radius:9px;padding:18px 20px;margin-top:8px;color:#fff";
  host.appendChild(box);
  var st={spacing:120, qaqc:1};
  function draw(){
    var cat,col,use,why;
    var ok=st.qaqc===1;
    if(st.spacing<=50 && ok){cat="MEASURED";col=C.navy;
      use="Can support Proven Reserves and a bankable feasibility study.";
      why="Spacing tight enough to confirm grade and geological continuity.";}
    else if(st.spacing<=150 && ok){cat="INDICATED";col=C.teal;
      use="Can support Probable Reserves and a feasibility study.";
      why="Continuity is reasonably assumed but not confirmed at "+
        "mining-selectivity scale.";}
    else if(st.spacing<=320){cat="INFERRED";col=C.bronze;
      use="Conceptual only. Cannot be converted to a Reserve or used in "+
        "feasibility economics.";
      why="Geological continuity is implied from limited data; grade is "+
        "estimated with low confidence.";}
    else {cat="EXPLORATION TARGET";col="#8a6d3b";
      use="Not a Mineral Resource at all - a range statement only.";
      why="Data too sparse to estimate tonnage and grade with any "+
        "geostatistical confidence.";}
    if(!ok && (cat==="MEASURED"||cat==="INDICATED")){
      why+=" QAQC failures further cap the category - you cannot certify "+
        "data you cannot trust.";
    }
    box.style.background=col;
    box.innerHTML="<div style='font-family:-apple-system,Segoe UI,sans-serif;"+
      "font-size:12px;letter-spacing:1.5px;opacity:.8'>RESULTING CATEGORY</div>"+
      "<div style='font-family:-apple-system,Segoe UI,sans-serif;font-size:26px;"+
      "font-weight:800;margin:3px 0 8px'>"+cat+"</div>"+
      "<div style='font-family:-apple-system,Segoe UI,sans-serif;font-size:13.5px;"+
      "line-height:1.55'><b>Why:</b> "+why+"<br><b>Economic use:</b> "+use+"</div>";
  }
  mkSlider(ctrls,"sp","Nominal drill spacing (m)",20,400,5,st.spacing,
    function(v){return v.toFixed(0)+" m";},function(v){st.spacing=v;draw();});
  mkSlider(ctrls,"qa","QAQC quality (0 = failing, 1 = passing)",0,1,1,st.qaqc,
    function(v){return v===1?"passing":"failing";},
    function(v){st.qaqc=v;draw();});
  draw();
}

/* ---------- boot ---------- */
document.addEventListener("DOMContentLoaded",function(){
  initCopy(); initQuiz();
  initVariogram(); initTopcut(); initGradeTonnage();
  initInterp(); initClassify();
});
