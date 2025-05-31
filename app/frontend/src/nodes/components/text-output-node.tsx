import { type NodeProps } from '@xyflow/react';
import { Bot, Loader2 } from 'lucide-react';
import { useRef, useState } from 'react';

import { Button } from '@/components/ui/button';
import { CardContent } from '@/components/ui/card';
import { useNodeContext } from '@/contexts/node-context';
import { type TextOutputNode } from '../types';
import { NodeShell } from './node-shell';
import { TextOutputDialog } from './text-output-dialog';
import { api } from '@/services/api';

export function TextOutputNode({
  data,
  selected,
  id,
  isConnectable,
}: NodeProps<TextOutputNode>) {  
  const { outputNodeData, agentNodeData, outputNodeOrderStatus } = useNodeContext();
  const [showOutput, setShowOutput] = useState(false);
  const abortControllerRef = useRef<(() => void) | null>(null);
  const nodeContext = useNodeContext();
  
  // Check if any agent is in progress
  const isProcessing = Object.values(agentNodeData).some(
    agent => agent.status === 'IN_PROGRESS'
  );
  
  const isOutputAvailable = !!outputNodeData;

  const isOrderComplete = outputNodeOrderStatus === 'COMPLETE';
  const isOrderError = outputNodeOrderStatus === 'ERROR';

  const handleViewOutput = () => {
    setShowOutput(true);
  }

  const handleOrder = () => {
    const tickers = Object.keys(outputNodeData?.decisions || {});
    tickers.forEach((ticker) => {
      const decision = outputNodeData?.decisions[ticker];
      if (decision.action === "buy") {
        abortControllerRef.current = api.runBuy(
          {
            ticker: ticker,
            qty: decision.quantity,
          },
          nodeContext
        );
      } else if (decision.action === "sell") {
        abortControllerRef.current = api.runSell(
          {
            ticker: ticker,
            qty: decision.quantity,
          },
          nodeContext
        );
      }
    });
  };

  return (
    <>
      <NodeShell
        id={id}
        selected={selected}
        isConnectable={isConnectable}
        icon={<Bot className="h-5 w-5" />}
        name={data.name || "Output"}
        description={data.description}
        hasRightHandle={false}
      >
        <CardContent className="p-0">
          <div className="border-t border-border p-3">
            <div className="flex flex-col gap-2">
              <div className="text-subtitle text-muted-foreground flex items-center gap-1">
                Results
              </div>
              <div className="flex gap-2">
                {isProcessing ? (
                  <Button 
                    variant="secondary"
                    className="w-full flex-shrink-0 transition-all duration-200 hover:bg-primary hover:text-primary-foreground active:scale-95 text-subtitle"
                    disabled
                  >
                    <Loader2 className="h-2 w-2 animate-spin" />
                    Processing...
                  </Button>
                ) : (
                  <Button 
                    variant="secondary"
                    className="w-full flex-shrink-0 transition-all duration-200 hover:bg-primary hover:text-primary-foreground active:scale-95 text-subtitle"
                    onClick={handleViewOutput}
                    disabled={!isOutputAvailable}
                  >
                   View Output
                  </Button>
                )}
              </div>
              <div className="text-subtitle text-muted-foreground flex items-center gap-1">
                Execute
              </div>
              <div className="flex gap-2">
                  {isOrderError ? (
                    <Button
                      variant="secondary"
                      className="w-full flex-shrink-0 transition-all duration-200 hover:bg-primary hover:text-primary-foreground active:scale-95 text-subtitle"
                      disabled
                    >
                      ERROR
                    </Button>
                  ) : isOrderComplete ? (
                    <Button
                      variant="secondary"
                      className="w-full flex-shrink-0 transition-all duration-200 hover:bg-primary hover:text-primary-foreground active:scale-95 text-subtitle"
                      disabled
                    >
                      Order Complete
                    </Button>
                  ) : (
                    <Button 
                      variant="secondary"
                      className="w-full flex-shrink-0 transition-all duration-200 hover:bg-primary hover:text-primary-foreground active:scale-95 text-subtitle"
                      onClick={handleOrder}
                      disabled={!isOutputAvailable}
                    >
                      Execute Order
                    </Button>
                  )}
              </div>
            </div>
          </div>
        </CardContent>
      </NodeShell>

      <TextOutputDialog 
        isOpen={showOutput} 
        onOpenChange={setShowOutput} 
        outputNodeData={outputNodeData} 
      />
    </>
  );
}
