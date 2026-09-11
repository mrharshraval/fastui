import * as React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { MoreHorizontal } from "lucide-react";
import type { DealModel } from "../api";

interface DealCardProps {
  deal: DealModel;
  stages: string[];
  onStageChange: (id: string, stage: string) => void;
  onDelete: (id: string, name: string) => void;
}

export function DealCard({ deal, stages, onStageChange, onDelete }: DealCardProps) {
  return (
    <Card className="bg-card rounded-xl shadow-none border border-border/20 group/card relative hover:border-border/60 transition-colors">
      <CardHeader className="pb-2 pt-3.5 px-3.5 flex flex-row items-start justify-between space-y-0 gap-2">
        <CardTitle className="text-sm font-medium leading-tight truncate flex-1">
          {deal.business_name}
        </CardTitle>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              aria-label="Deal options"
              className="size-6 rounded-full flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-accent/80 transition-colors opacity-0 group-hover/card:opacity-100 cursor-pointer shrink-0 -mt-1 -mr-1"
            >
              <MoreHorizontal size={14} />
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-40">
            {stages
              .filter((s) => s !== deal.stage)
              .map((st) => (
                <DropdownMenuItem
                  key={st}
                  onClick={() => onStageChange(deal.id, st)}
                  className="text-xs cursor-pointer"
                >
                  Move to {st}
                </DropdownMenuItem>
              ))}
            <DropdownMenuItem
              onClick={() => onDelete(deal.id, deal.business_name)}
              className="text-destructive text-xs font-medium cursor-pointer"
            >
              Delete
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </CardHeader>
      <CardContent className="px-3.5 pb-3.5 pt-0">
        <div className="flex items-center justify-between">
          {deal.value ? (
            <span className="text-xs font-semibold">${deal.value.toLocaleString("en-US")}</span>
          ) : (
            <span className="text-xs text-muted-foreground">—</span>
          )}
          {deal.probability ? (
            <span className="text-xs text-muted-foreground">{deal.probability}%</span>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}
