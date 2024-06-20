import {expect, jest, test} from '@jest/globals';
import { lstrip, PIDSplitter } from '../src/pidsplitter.js';


const lstrip_cases = [
    ["", " :/", ""],
    ["a/: ", " :/", "a/: "],
    [" /:a", " :/", "a"],
]

describe("LStrip cases", () => {
   test.each(lstrip_cases)(
       "LStrip '%s'", (a,c, b) => {
           expect(lstrip(a, c)).toBe(b);
       }
   )
});


const pid_cases = [
    ["ark", {scheme:"ark", prefix:null, value: null, content:null}],
    ["ark:", {scheme:"ark", prefix:null, value: null, content:null}],
    ["ark://", {scheme:"ark", prefix:null, value: null, content:null}],
    ["ark:/12345/foo", {scheme:"ark", prefix:"12345", value:"foo", content:"12345/foo"}],
]


describe("Split pids", () => {
    test.each(pid_cases)(
        "Split %s", (pid, tc) => {
            const splt = new PIDSplitter(pid);
            expect(splt.scheme).toBe(tc.scheme);
            expect(splt.prefix).toBe(tc.prefix);
            expect(splt.value).toBe(tc.value);
            expect(splt.content).toBe(tc.content);
        }
    )
});

