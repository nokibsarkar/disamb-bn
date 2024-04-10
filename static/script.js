function init({ disambuiguableClass = 'disambiguable', candidates = [], language = 'bn', newPageExtractorPattern = /(.+) \(পাতার অস্তিত্ব নেই\)$/, title = '' }) {
    const url = `https://${language}.wikipedia.org/w/api.php`
    const qs = new URLSearchParams({ title, language })
    const pageLoadIcon = document.getElementById('page-load-icon');
    const csrfElement = document.getElementById('csrf');
    const loadButton = document.getElementById('load-button');
    const submitLoadIcon = document.getElementById('submit-load-icon')
    const previewLoadIcon = document.getElementById('preview-load-icon')
    const contentElement = document.getElementById('content');
    const previewElement = document.getElementById('preview');
    const submitButton = document.getElementById('submit');
    const languageSelector = document.getElementById('language');
    const titleInput = document.getElementById('title');
    const submitStatus = document.getElementById('submit-status');
    titleInput.value = title;
            
    const url2 = "/api/disambiguate?" + qs.toString()
    pageLoadIcon.style.display = 'inline-block'
    const disambiguablesMap = {};
    async function loadPreview(id) {
        if (disambiguablesMap[id].preview) {
            return disambiguablesMap[id].preview;
        }

        previewLoadIcon.style.display = 'inline-block'
        previewElement.innerHTML = previewLoadIcon.outerHTML

        previewElement.style.top = `${STATE.currentSelectedY}px`;
        previewElement.style.left = `${STATE.currentSelectedX}px`;
        previewElement.style.display = 'block'
        const params = {
            "action": "parse",
            "format": "json",
            "page": id,
            "prop": "text",
            "utf8": 1,
            "origin": "*",
            "formatversion": "2"
        }
        const queryString = new URLSearchParams(params).toString();
        const response = await fetch(`${url}?${queryString}`);
        const data = await response.json();
        const content = data.parse.text;

        disambiguablesMap[id].preview = content;

    }
    
    const STATE = {
        currentSelected: null,
        currentSelectedX: 0,
        currentSelectedY: 0,
    }
    async function showPreview(id) {
        const content = disambiguablesMap[id].preview;
        previewElement.innerHTML = content;
        previewElement.style.display = 'block';
        previewElement.style.top = `${STATE.currentSelectedY}px`;
        previewElement.style.left = `${STATE.currentSelectedX}px`;
        [...previewElement.getElementsByTagName('a')].forEach((a) => {
            a.onclick = function (event) {
                event.preventDefault();
                event.stopPropagation();
                let title = a.getAttribute('title');
                if (!title) {
                    return;
                }
                const isNew = a.classList.contains('new');
                if (isNew) {
                    const match = title.match(newPageExtractorPattern);
                    if (match) {
                        title = match[1];
                    }
                }
                if (STATE.currentSelected) {
                    STATE.currentSelected.outerHTML = title;
                    STATE.currentSelected = null;
                    STATE.currentSelectedX = 0;
                    STATE.currentSelectedY = 0;
                    closePreview();
                }

            };
        });

    }
    function closePreview() {
        previewElement.style.display = 'none';

    }
    fetch(url2).then(res => res.json())
        .then(r => {
            pageLoadIcon.style.display = 'none';
            loadButton.onclick = e => {
                e.preventDefault();
                init({
                    candidates: r.candidates,
                    title: titleInput.value,
                    language: r.language
                });
            }
            contentElement.innerHTML = r.content;
            const disambiguables = document.getElementsByClassName(disambuiguableClass);
            for (const candidate of r.candidates) {
                disambiguablesMap[candidate] = {
                    id: candidate,
                    preview: null,
                }
            }
            candidates = new Set(candidates);
            
            
            
            
            for (const disamb of disambiguables) {
                disamb.addEventListener('click', function (event) {
                    const source = event.target;
                    event.stopPropagation();
                    const id = source.dataset.index;
                    STATE.currentSelected = source;
                    STATE.currentSelectedX = event.clientX;
                    STATE.currentSelectedY = event.clientY;
                    loadPreview(id).then(() => showPreview(id));
                });
                document.addEventListener('click', function (event) {
                    if (event.target !== STATE.currentSelected || event.target !== previewElement) {
                        closePreview();
                    }
                });
                previewElement.addEventListener('click', function (event) {
                    event.stopPropagation();
                });
            }
            submitButton.onclick = function (event) {
                const title = titleInput.value;
                const lang = languageSelector.value;
                const content = contentElement.innerText;
                const params = {
                    title: title,
                    text: content,
                    language: lang,
                }
                const url = document.location.toString();
                submitLoadIcon.style.display = 'inline-block'
                fetch(url, {
                    method: 'POST',
                    body: JSON.stringify(params),
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include'
                }).then((response) => response.json()).then((data) => {
                    submitLoadIcon.style.display = 'none';
                    if(data.edit.result == 'Success'){
                        submitStatus.innerHTML = '<i style="color:green">Success</i>';
                        
                    } else {
                        submitStatus.innerHTML = '<i style="color:red">Error</i>';
                    }
                    setTimeout(() => submitStatus.innerHTML = "", 5000);
                });
            };
        });



}