export type GuidedReport={status:'blocked'|'requires_validation';checks:{name:string;status:'checked'|'blocked'|'caution'|'unknown';detail:string;action:string}[];metrics:null|{delta_mjy:number;random_error_mjy:number;days:number};limitations:string[]};

// A formal random error is not a calibrated variability significance.
// Never turn a large ratio, or the absence of a blocking check, into a discovery.
export function guidedVerdict(report:GuidedReport):'unavailable'|'unconfirmed'{
 if(report.status==='blocked'||!report.metrics||!Number.isFinite(report.metrics.delta_mjy)||!Number.isFinite(report.metrics.random_error_mjy)||report.metrics.random_error_mjy<=0)return 'unavailable';
 return 'unconfirmed';
}
