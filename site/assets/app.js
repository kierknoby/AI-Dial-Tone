const menu=document.querySelector('.menu-button');
const nav=document.querySelector('#primary-nav');
if(menu && nav){
  menu.addEventListener('click',()=>{
    const open=menu.getAttribute('aria-expanded')!=='true';
    menu.setAttribute('aria-expanded',String(open));
    menu.setAttribute('aria-label',open?'Close navigation':'Open navigation');
    nav.classList.toggle('menu-open',open);
  });
  nav.addEventListener('click',(event)=>{
    if(event.target.closest('a')){ menu.setAttribute('aria-expanded','false');nav.classList.remove('menu-open'); }
  });
}
let toastTimer;
export function announce(text){
  const el=document.querySelector('[data-toast]');
  if(!el)return;
  el.textContent=text;el.classList.add('shown');clearTimeout(toastTimer);
  toastTimer=setTimeout(()=>el.classList.remove('shown'),2200);
}
export async function copyText(value){
  try{await navigator.clipboard.writeText(value);announce('Copied to clipboard');return true;}
  catch{announce('Clipboard unavailable. Select the text to copy.');return false;}
}
document.querySelectorAll('[data-copy-target]').forEach(button=>{
  button.addEventListener('click',()=>{
    const target=document.getElementById(button.dataset.copyTarget);
    if(target)copyText(target.textContent);
  });
});
