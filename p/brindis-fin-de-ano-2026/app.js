document.addEventListener('play',function(e){document.querySelectorAll('video').forEach(function(v){if(v!==e.target)v.pause()})},true);
var lb=document.getElementById('lb'),li=lb.querySelector('img');
document.querySelectorAll('.ph').forEach(function(b){b.addEventListener('click',function(){li.src=b.dataset.src;lb.showModal()})});
lb.addEventListener('click',function(){lb.close()});
