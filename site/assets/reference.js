// Static, local-only documentation enhancements. No network calls or user analytics.
const search=document.getElementById('ref-search');
if(search){
  const cards=Array.from(document.querySelectorAll('.ref-card'));
  const count=document.getElementById('ref-search-count');
  const empty=document.getElementById('ref-search-empty');
  const filter=()=>{
    const query=search.value.trim().toLocaleLowerCase();let shown=0;
    for(const card of cards){
      const visible=!query || (card.dataset.search||card.textContent.toLocaleLowerCase()).includes(query);
      card.hidden=!visible;if(visible)shown++;
    }
    if(count)count.textContent=`${shown} of ${cards.length} chapters`;
    if(empty)empty.hidden=shown!==0;
  };
  search.addEventListener('input',filter);
}
for(const block of document.querySelectorAll('.ref-markdown pre')){
  const button=document.createElement('button');
  button.type='button';button.className='ref-code-copy';button.textContent='Copy';
  button.setAttribute('aria-label','Copy code example');
  button.addEventListener('click',async()=>{
    try{
      await navigator.clipboard.writeText(block.querySelector('code')?.textContent||'');
      button.textContent='Copied';
    }catch{button.textContent='Select to copy';}
  });
  block.append(button);
}
