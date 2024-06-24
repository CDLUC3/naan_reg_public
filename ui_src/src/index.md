---
style: style.css
---

<link href="npm:gridjs/dist/theme/mermaid.min.css" rel="stylesheet">

# NAAN Registry Records

The NAAN Registry maintains the authoritative list of Name Assigning Authority Numbers which are the numeric 
prefixes used by ARK identifiers. A NAAN may be allocated to an organization on request.

```js
import {PIDSplitter} from './pidsplitter.js';
import {NAANRecords} from './naan_records.js';

import { Grid, html as ghtml } from 'npm:gridjs';

const dateStr = (v) => {
    const d = new Date(v);
    return d.toISOString().split('T')[0]
}

const naans_url = "https://cdluc3.github.io/naan_reg_public/naan_records.json";
const records =  await fetch(naans_url)
    .then((response) => response.json())
    .then((data) => {return new NAANRecords(data)})
    .catch((reason) => {
        const tnow = new Date();
        view(html`<pre>ERROR: Could not load ${naans_url}</pre>`);
        return new NAANRecords([{"when":dateStr(tnow)}]);
    });

const selected_record = Mutable(0);
const setSelectedRecord = (v) => {
    selected_record.value = v;
}
const getSelectedRecord = () => {
    return selected_record.value;
}
```

There are currently ${records.length.toLocaleString()} NAAN records, with the first issued on ${dateStr(records.earliest)} and the most 
recent on ${dateStr(records.latest)}.

```js
const histogram = await vl.render({
    spec: {
        "$schema": "https://vega.github.io/schema/vega-lite/v5.json",
        "width": -1,
        "height": 250,
        "autosize": {"type": "fit", "contains": "padding"},
        "data": {"values": records.timeCounts},
        "mark": "line",
        "encoding": {
            "x": {
                "field": "date",
                "type": "temporal",
                "title": "Date",
            },
            "y": {
                "field": "count",
                "title": "Number of records",
                "type": "quantitative"
            }         
        }
    }
})
display(resize((width) => {
  histogram.value.width(Math.min(640 - 16 * 2, width));
  histogram.value.run();
  return histogram;
}));
```
**Figure 1.** Number of NAAN records registered over time. The first registration was recorded on ${dateStr(records.earliest)} 
and the most recent on ${dateStr(records.latest)}. 


A list of the NAAN records is provided below. This list is also available in other formats for programmatic use:

- JSON: ${html `<a href='${naans_url}'>naan_records.json</a>`}
- YAML: [n2t_full_prefixes.yaml](https://legacy-n2t.n2t.net/e/n2t_full_prefixes.yaml)


<div class="card">

**Table 1.** A listing of the ${records.length.toLocaleString()} NAAN records maintained by the NAAN registry. The public
information for a record may be seen below by clicking on the corresponding prefix (NAAN) value. The search box can be used 
to filter the displayed records. 

<div id="datatable"></div>

</div>

```js
const userpid = Inputs.text({value:"ark:/12345/foo/baz"});

const splitter = new PIDSplitter(userpid.value);

const recordHtml = (naan) => {
    const record = records.get(naan);
    if (record) {
        return html`
            <div >
                <dl>
                    <dt>Prefix:</dt><dd><code>${record.what}</code></dd>
                    <dt>Created:</dt><dd>${record.created}</dd>
                    <dt>Agency:</dt><dd>${record.name}</dd>
                    <dt>Where:</dt><dd><a href="${record.where}" target="_blank">${record.where}</a></dd>
                    <dt>Target:</dt><dd><code>${record.target.url} (${record.target.http_code})</code></dd>
                    <dt>
                </dl>
           </div>
        `;
    }
    return html`No record selected.`;
}

const recordJSON = (naan) => {
    const record = records.get(naan);
    return html`<pre style="overflow:scroll">${record.jsonstr}</pre>`
}

const datatable = new Grid({
    columns:[{
        id: "what",
        name: "Prefix",
        attributes: (cell) => {
            if (cell) {
                return {
                  'onmouseover': ()=>{},
                  'onclick': ()=>{setSelectedRecord(cell)},  
                  'style': 'cursor: pointer'
                };
            }
        },
        formatter: (v, row)=> {
            return ghtml(`<code>${v}</code>`);
        }
    }, {
        data: (row) => dateStr(row.when),
        name: "Created"
    }, {
        data: (row) => {
            let name = row.who.name;
            if (row.who.acronym) {
                name = `${name} (${row.who.acronym})`;
            }
            return name;
        },
        name: "Who",
        formatter: (v, row) => {
            const record = records.get(row.cells[0].data);
            return ghtml(`<a href='${record.where}' target='_blank'>${v}</a>`);
        }
    }
    ],
    fixedHeader: true,
    height: '600px',
    maxWidth: '640px',
    search: true,
    sort: true,
    data: records.data,
})
const ele = document.getElementById("datatable");
if (ele) {
    ele.innerHTML = "";
}

datatable.render(document.getElementById("datatable"));
setSelectedRecord("12025");
```

<div class="grid grid-cols-2">
    ${recordHtml(selected_record)}
    ${recordJSON(selected_record)}
</div>
