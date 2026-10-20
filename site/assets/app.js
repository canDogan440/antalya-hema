(function(){
  // opened straight from disk (file://): folder links like "meyer-1570/" need an explicit index.html
  if(location.protocol==='file:'){
    document.querySelectorAll('a[href]').forEach(function(a){
      var h=a.getAttribute('href');
      if(/^(https?:|tel:|mailto:|#)/.test(h))return;
      var i=h.indexOf('#'),path=i<0?h:h.slice(0,i),hash=i<0?'':h.slice(i);
      if(path===''||path==='.')path='./';
      if(path.slice(-1)==='/')a.setAttribute('href',path+'index.html'+hash);
    });
  }

  // mobile menu
  var btn=document.querySelector('.menu-btn'),nav=document.getElementById('nav');
  if(btn&&nav){
    btn.addEventListener('click',function(){var o=nav.classList.toggle('open');btn.setAttribute('aria-expanded',o);});
    nav.addEventListener('click',function(e){if(e.target.tagName==='A'){nav.classList.remove('open');btn.setAttribute('aria-expanded','false');}});
  }

  // atlas: section filter
  var chips=[].slice.call(document.querySelectorAll('.atlas .chip'));
  function filter(f){
    chips.forEach(function(c){c.classList.toggle('on',c.dataset.f===f);c.setAttribute('aria-pressed',c.dataset.f===f);});
    document.querySelectorAll('.atlas .group').forEach(function(g){g.hidden=!(f==='all'||g.dataset.group===f);});
    document.querySelectorAll('.atlas .toc a').forEach(function(a){a.hidden=!(f==='all'||a.dataset.group===f);});
  }
  chips.forEach(function(c){c.addEventListener('click',function(){filter(c.dataset.f);});});

  // atlas: lightbox
  var lb=document.getElementById('lb');
  if(!lb)return;
  var img=document.getElementById('lbimg'),cap=document.getElementById('lbcap'),list=[],idx=0;
  function show(){
    var el=list[idx],im=el.querySelector('img');
    img.src=im.dataset.full||im.src;img.alt=el.dataset.cap;
    cap.textContent=el.dataset.cap;
    var s=document.createElement('small');s.textContent=el.dataset.meta+'  ·  '+(idx+1)+' / '+list.length;cap.appendChild(s);
  }
  function open(el){list=[].slice.call(el.closest('[data-gal]').querySelectorAll('.card'));idx=list.indexOf(el);show();lb.hidden=false;document.body.style.overflow='hidden';document.getElementById('lbx').focus();}
  function close(){lb.hidden=true;document.body.style.overflow='';if(list[idx])list[idx].focus();}
  document.querySelectorAll('.atlas .card').forEach(function(el){
    el.addEventListener('click',function(){open(el);});
    el.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();open(el);}});
  });
  function step(d){idx=(idx+d+list.length)%list.length;show();}
  document.getElementById('lbx').onclick=close;
  document.getElementById('lbp').onclick=function(){step(-1);};
  document.getElementById('lbn').onclick=function(){step(1);};
  lb.addEventListener('click',function(e){if(e.target===lb)close();});
  document.addEventListener('keydown',function(e){
    if(lb.hidden)return;
    if(e.key==='Escape')close();
    if(e.key==='ArrowLeft')step(-1);
    if(e.key==='ArrowRight')step(1);
  });
})();
