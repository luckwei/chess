type Position = [number, number];

function in_bounds(pos: Position): boolean {
  return Math.max(...pos) <= 7 && Math.min(...pos) >= 0;
}

function in_bounds_filter(lst: Position[]): Position[] {
  return lst.filter((e) => in_bounds(e));
}

enum Color {
  NONE = "none",
  WHITE = "white",
  BLACK = "black",
}

namespace Color {
  export function dir(color: Color): number {
    return color == Color.WHITE ? -1 : color == Color.BLACK ? 1 : 0;
  }

  export function other(color: Color): Color {
    return color == Color.WHITE
      ? Color.BLACK
      : color == Color.BLACK
      ? Color.WHITE
      : Color.NONE;
  }

  export function backRank(color: Color): number {
    return color == Color.WHITE ? 7 : color == Color.BLACK ? 0 : -1;
  }
}

abstract class Piece {
  readonly isPiece: boolean
  constructor(readonly color: Color) {
    this.isPiece = color != Color.NONE
  }
  abstract moves(board: any, pos: any): any[];

}

class Empty extends Piece {
  constructor(...args:any[]) {
    super(Color.NONE)
  }
  // Implement bool: bool implemented as isPiece property
  moves(board: any, pos: any): any[] {
    return []
  }

}


// dir, other, back_rank missing

export { Color };

