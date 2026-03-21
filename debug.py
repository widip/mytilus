from pathlib import Path

from mytilus.computer import Box, ComputableFunction, ProgramTy, Ty
from mytilus.metaprog import (
    MetaprogramComputation,
    MetaprogramFunctor,
    ProgramComputation,
    ProgramFunctor,
)
from mytilus.state import Process, ProgramClosedCategory, fixed_state, simulate


def large_diagram():
    X, A, B, C, D = Ty("X"), Ty("A"), Ty("B"), Ty("C"), Ty("D")
    H_ty, L_ty = ProgramTy("H"), ProgramTy("L")

    high_level = ProgramClosedCategory(H_ty)
    low_level = ProgramClosedCategory(L_ty)

    # Stateful execution in the same language composed for several rounds.
    stateful_chain = (
        high_level.execution(A, B)
        >> high_level.execution(B, C)
        >> high_level.execution(C, D)
    )

    # One execution step followed by an interpreted high-level computation.
    interpreter_chain = (
        high_level.execution(A, B)
        >> ProgramFunctor()(ProgramComputation("H", L_ty, H_ty, B, C))
    )

    # One execution step followed by a metaprogram rewrite / partial evaluation.
    compiler_chain = (
        high_level.execution(A, B)
        >> MetaprogramFunctor()(MetaprogramComputation("H", L_ty, L_ty, H_ty, B, C))
    )

    # A plain computation lifted to a process, then simulated in the high-level
    # program state space, and executed once more.
    process_chain = (
        fixed_state(ComputableFunction("worker", X, A, B))
        >> simulate(Process("machine", X, B, C), Box("embed", X, H_ty))
        >> high_level.execution(C, D)
    )

    # A separate low-level execution pipeline for contrast with the H-language.
    low_level_chain = low_level.execution(A, B) >> low_level.execution(B, C)

    # Tensor the pipelines together so the rendered figure shows several linked
    # Chapter 6/7 stories in one large diagram.
    return (
        stateful_chain
        @ interpreter_chain
        @ compiler_chain
        @ process_chain
        @ low_level_chain
    )


if __name__ == "__main__":
    output_path = Path("debug.svg")
    large_diagram().draw(path=str(output_path))
    print(output_path)
