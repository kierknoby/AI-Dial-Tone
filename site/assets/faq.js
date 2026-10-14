// A progressive enhancement to fully visible, semantic HTML <details> FAQs.
// No analytics, network calls, or user input is submitted to a server.
const search=document.getElementById('faq-search');
if(search){
  const categories=[...document.querySelectorAll('.faq-category')];
  const items=[...document.querySelectorAll('.faq-item')];
  const count=document.getElementById('faq-count');
  const empty=document.getElementById('faq-empty');
  const clear=document.getElementById('faq-clear');
  function update(){
    const term=search.value.trim().toLocaleLowerCase();let shown=0;
    for(const item of items){
      const visible=!term || item.dataset.search.includes(term);
      item.hidden=!visible;
      if(!visible)item.open=false;
      if(visible)shown++;
    }
    for(const cat of categories)cat.hidden=![...cat.querySelectorAll('.faq-item')].some(i=>!i.hidden);
    count.textContent=`${shown} of ${items.length} questions`;empty.hidden=shown!==0;
    clear.disabled=!term;
  }
  search.addEventListener('input',update);
  clear.addEventListener('click',()=>{search.value='';update();search.focus();});
  document.getElementById('faq-expand').addEventListener('click',()=>{for(const i of items)if(!i.hidden)i.open=true;});
  document.getElementById('faq-collapse').addEventListener('click',()=>{for(const i of items)i.open=false;});
  update();
}
