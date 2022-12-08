export type Position = [number, number];

export function in_bounds(pos: Position): boolean {
  return Math.max(...pos) <= 7 && Math.min(...pos) >= 0;
}

export function in_bounds_filter(lst: Position[]): Position[] {
  return lst.filter((e) => in_bounds(e));
}

export enum Color {
  NONE = "none",
  WHITE = "white",
  BLACK = "black",
}

export namespace Color {
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

export abstract class Piece {
  readonly isPiece: boolean;

  constructor(readonly color: Color) {
    this.isPiece = color != Color.NONE;
  }
  abstract moves(board: any, pos: Position): Move[];
}

export class Empty extends Piece {
  constructor() {
    super(Color.NONE);
  }
  // Implement bool: bool implemented as isPiece property
  moves(board: any, pos: Position): Move[] {
    return [];
  }
}
//TODO: CREATE OTHER PIECE TYPES
export enum Flag {
  NONE,
  ENPASSANT_TRGT,
  ENPASSANT,
  CASTLE_QSIDE,
  CASTLE_KSIDE,
  LOSE_KING_PRIV,
  LOSE_ROOK_PRIV,
  PROMOTION,
  // Flag loses bool property
}
export class Move extends Array<number> {
  constructor(pos: Position, public flag: Flag = Flag.NONE) {
    super();
    this.push(...pos);
  }

  add(other: Move | Position) {
    return new Move([this[0] + other[0], this[1] + other[1]], this.flag);
  }
  // __add__/__radd__/delta implementation is now replaced by add method
}


export class CastlingPermission extends Map{
  private static FENCASTLING = new Map<[Color, Flag], string>([
    [[Color.WHITE, Flag.CASTLE_KSIDE], "K"],
    [[Color.WHITE, Flag.CASTLE_QSIDE], "Q"],
    [[Color.BLACK, Flag.CASTLE_KSIDE], "k"],
    [[Color.BLACK, Flag.CASTLE_QSIDE], "q"],
  ]);

  constructor(castlingPermStr: string = "KQkq") {
    super();
    CastlingPermission.FENCASTLING.forEach((castlingChar, colorFlag) => {
      this.set(colorFlag, castlingPermStr.includes(castlingChar))
    })
  }

  falsify(color: Color, flag: Flag = Flag.LOSE_KING_PRIV) {
    if (flag == Flag.LOSE_KING_PRIV){
      this.set([color, Flag.CASTLE_QSIDE], false)
      this.set([color, Flag.CASTLE_QSIDE], false)
      return
    }
    this.set([color, flag], false)
  }
  set(key: [Color, Flag], value: boolean) {
    return super.set(key.toString(), value)
  }
  get(key: [Color, Flag]) {
    return super.get(key.toString())
  }
}

//TODO: POPULATE WITH PIECE TYPES
const FEN_MAP = new Map<string, Piece>([[" ", new Empty()]]);

export class Board extends Map{
  colorMove: Color;
  castlingPermission: CastlingPermission;
  empassantTarget: Position;
  allMovesCache: Map<Position, Piece>;

  constructor(
    fenString = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
  ) {
    super();

    //random

    const splitStr = fenString.replace("/", "").split(" ");
    let [boardConfig, colorMove, castlingPerm, enpassantTrgt, ...rest] =
      splitStr;
    this.colorMove = colorMove == "w" ? Color.WHITE : Color.BLACK;
    this.castlingPermission = new CastlingPermission(castlingPerm);
    this.empassantTarget = [
      8 - parseInt(enpassantTrgt[1]),
      "abcdefgh".indexOf(enpassantTrgt[0]),
    ];
    this.allMovesCache = new Map<Position, Piece>();
    [..."12345678"].forEach(i => {
      boardConfig = boardConfig.replace(i, " ".repeat(parseInt(i)))
    })
    //TODO: CHECK IF SETTING KEY AS ARRAY LEADS TO ERROR
    for (const [index, pieceChar] of [...boardConfig].entries()) {
      const pos: Position = [Math.floor(index / 8), index % 8];
      this.allMovesCache.set(pos, FEN_MAP.get(pieceChar) ?? new Empty());
    }

    //TODO: IMPLEMENT OTHER METHODS
    
  }
  set(key: Position, value: Piece) {
    return super.set(key.toString(), value)
  }
  get(key: Position) {
    return super.get(key.toString())
  }
}

