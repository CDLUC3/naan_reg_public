/**
 * Implements a PID splitter
 */

export function lstrip(s, chars) {
    while (s.length > 0 && chars.indexOf(s.charAt(0)) !== -1) {
        s = s.substring(1);
    }
    return s;
}

export class PIDSplitter {
    constructor (pidstr) {
        this.pid = "";
        this.scheme = "";
        this.content = null;
        this.prefix = null;
        this.value = null;
        this.split(pidstr);
    }

    split(pid) {
        this.pid = pid;
        this.scheme = "";
        this.content = null;
        this.prefix = null;
        this.value = null;
        let _parts = this.pid.split(":", 2);
        this.scheme = _parts[0].trim().toLowerCase();
        if (_parts.length < 2) {
            return this;
        }
        this.content = lstrip(_parts[1], ' /:');
        this.content = this.content.trim();
        if  (this.content === "") {
            this.content = null;
            return this;
        }
        _parts = this.content.split("/", 2);
        this.prefix = _parts[0].trim();
        if (_parts.length < 2) {
            return this;
        }
        this.value = lstrip(_parts[1], " ,/");
        this.value = this.value.trim();
        return this;
    }

    fillTemplate(template) {
        let res = template.replace(/{pid}/, this.pid);
        res = res.replace(/{scheme}/, this.scheme);
        res = res.replace(/{content}/, this.content);
        res = res.replace(/{prefix}/, this.prefix);
        res = res.replace(/{value}/, this.value);
        return res;
    }
}

