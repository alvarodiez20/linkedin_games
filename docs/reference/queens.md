# Queens

::: linkedin_games.queens.extractor
    options:
      members:
        - QueensState
        - extract_state

::: linkedin_games.queens.solver
    options:
      members:
        - QueensSolution
        - solve
        - validate_solution
        - format_solution

::: linkedin_games.queens.player
    options:
      members:
        - play_solution
