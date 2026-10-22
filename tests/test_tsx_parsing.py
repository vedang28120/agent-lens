import pytest
from agent_lens.core.parser import CodeParser


def test_tsx_arrow_function_and_interface_parsing():
    tsx_code = """
import React, { useState } from 'react';

export interface ButtonProps {
    label: string;
    onClick: () => void;
}

export const ActionButton = ({ label, onClick }: ButtonProps) => {
    return (
        <button onClick={onClick} className="btn-primary">
            {label}
        </button>
    );
};

export class ModalDialog extends React.Component {
    close() {
        console.log("Closing modal");
    }
}
"""
    res = CodeParser.parse_file("Component.tsx", content=tsx_code)

    assert res.language == "tsx"
    assert res.parse_error is None
    sym_names = [s.name for s in res.symbols]
    assert "ActionButton" in sym_names
    assert "ModalDialog" in sym_names

    # Check that ActionButton was captured
    btn_sym = next(s for s in res.symbols if s.name == "ActionButton")
    assert btn_sym.kind == "function"
    assert "ActionButton" in btn_sym.signature
