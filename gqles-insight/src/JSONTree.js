import React from 'react';

import JSONTree  from 'react-json-tree';


export function loadB64JSONOrNothing(data) {
    try {
        return JSON.parse(atob(data));
    } catch (err) {
        console.log({error: err});
        return undefined;
    }
}


export function JSONView(props) {
    const github = {
        scheme: "Github",
        author: "Defman21",
        base00: "#ffffff" ,
        base01: "#f5f5f5" ,
        base02: "#c8c8fa" ,
        base03: "#969896" ,
        base04: "#e8e8e8" ,
        base05: "#333333" ,
        base06: "#ffffff" ,
        base07: "#ffffff" ,
        base08: "#ed6a43" ,
        base09: "#0086b3" ,
        base0A: "#795da3" ,
        base0B: "#183691" ,
        base0C: "#183691" ,
        base0D: "#795da3" ,
        base0E: "#a71d5d" ,
        base0F: "#333333",
    };

    return (
        <JSONTree
          theme={github}
          invertTheme={false}
          {...props}
        />
    );
}

export default JSONView;
