/**
 * Implements some convenience for handling the naan recods.
 */

export class NAANRecord {
    constructor (record) {
        Object.assign(this, record);
    }

    get name() {
        let namestr = this.who.name
        if (this.who.acronym) {
            namestr = `${namestr} (${this.who.acronym})`
        }
        return namestr;
    }

    get created() {
        const d = new Date(this.when);
        return d.toISOString().split('T')[0]
    }

    get jsonstr() {
        return JSON.stringify(this, null, 2);
    }

}

export class NAANRecords {
    constructor (records) {
        this.data = records.data;
        this.metadata = records.metadata;
        this._index = this.buildIndex();
        this.timeCounts = this.buildTimeCounts();
    }

    buildIndex() {
        // Build a reverse lookup naan -> offset in data array.
        const res = {}
        let n = 0;
        for (const _record of this.data) {
            res[_record.what] = n;
            n = n + 1;
        }
        return res;
    }

    buildTimeCounts() {
        // Build list of date, naan_record_count
        const res = [];
        let n = 1;
        for (const r of this.data.sort((a, b) => {
            const ad = new Date(a.when);
            const bd = new Date(b.when);
            return ad - bd;
        })) {
            res.push(
                {
                    "date":  new Date(r.when),
                    "count": n
                }
            )
            n += 1;
        }
        return res;
    }

    get(naan) {
        // retrieve a naan record
        return new NAANRecord(this.data[this._index[naan]]);
    }

    get length() {
        return this.data.length;
    }

    get earliest() {
        return this.timeCounts[0].date;
    }

    get latest() {
        return this.timeCounts[this.timeCounts.length-1].date;
    }

}