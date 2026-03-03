declare module "react-material-symbols" {
  import { FC } from "react";
  interface MaterialSymbolProps {
    symbol: string;
    size?: number;
    className?: string;
  }
  export const MaterialSymbol: FC<MaterialSymbolProps>;
}
