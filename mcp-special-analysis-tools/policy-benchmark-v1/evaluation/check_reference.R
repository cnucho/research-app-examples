#!/usr/bin/env Rscript
# Independent numerical reference, not a research-validity classifier.
# Usage: Rscript check_reference.R request.json result.json
# The application worker is never sourced or executed. Gaussian models use QR
# and explicit covariance arithmetic; specialized estimators call their public
# R packages directly with the supplied plan. Comparisons use abs+relative 1e-8
# tolerance; each check reports the resulting absolute bound.

argv <- commandArgs(trailingOnly = TRUE)
if (!requireNamespace("jsonlite", quietly = TRUE)) {
  cat('{"method":null,"checks":[{"id":"jsonlite_available","actual":false,"expected":true,"tolerance":0,"match":false}],"passed":false}')
  quit(status = 1L)
}
checks <- list()
method <- NULL
vec <- function(x) unlist(x, use.names = FALSE)
strings <- function(x) as.character(vec(x))
package <- function(x) {
  if (!requireNamespace(x, quietly = TRUE)) stop(paste("Reference package unavailable:", x))
}
check <- function(id, actual, expected, tolerance = 1e-8) {
  # JSON null corresponds to undefined numerical quantities, not zero.
  av <- if (is.null(actual)) NA_real_ else vec(actual)
  ev <- if (is.null(expected)) NA_real_ else vec(expected)
  numeric_pair <- is.numeric(av) && is.numeric(ev)
  bound <- if (numeric_pair && length(ev)) tolerance * pmax(1, abs(ev)) else 0
  if (numeric_pair) {
    same_length <- length(av) == length(ev)
    same_missing <- same_length && identical(is.na(av), is.na(ev))
    finite <- is.finite(ev)
    same_nonfinite <- same_length && all(is.na(ev) | finite | av == ev, na.rm = TRUE)
    matched <- same_missing && same_nonfinite && all(is.finite(av[finite])) &&
      all(abs(av[finite] - ev[finite]) <= bound[finite])
  } else {
    matched <- identical(av, ev)
  }
  checks[[length(checks) + 1L]] <<- list(id = id, actual = actual,
    expected = expected, tolerance = if (length(bound) == 1L) bound else as.list(bound),
    match = isTRUE(matched))
  invisible(matched)
}
records <- function(rows) {
  if (!is.list(rows) || !length(rows)) stop("Expected a nonempty array of rows")
  keys <- unique(unlist(lapply(rows, names), use.names = FALSE))
  out <- lapply(keys, function(k) {
    vals <- lapply(rows, function(r) r[[k]])
    scalar <- vapply(vals, function(z) is.null(z) || length(z) == 1L, logical(1))
    if (!all(scalar)) stop("Rows contain nonscalar cells")
    present <- Filter(Negate(is.null), vals)
    if (!length(present)) return(rep(NA_real_, length(rows)))
    kind <- if (all(vapply(present, is.numeric, logical(1)))) "numeric" else
      if (all(vapply(present, is.character, logical(1)))) "character" else
      if (all(vapply(present, is.logical, logical(1)))) "logical" else stop("Mixed column types")
    missing <- switch(kind, numeric = NA_real_, character = NA_character_, logical = NA)
    unlist(lapply(vals, function(z) if (is.null(z)) missing else z), use.names = FALSE)
  })
  names(out) <- keys
  as.data.frame(out, stringsAsFactors = FALSE, check.names = FALSE)
}
lookup <- function(rows, id) {
  hit <- which(vapply(rows, function(x) identical(x$id, id), logical(1)))
  if (length(hit) != 1L) stop(paste("Missing or duplicate result record:", id))
  rows[[hit]]
}

run_reference <- function(request, result) {
  plan <- request$plan
  method <<- plan$method
  if (!is.null(result$error)) stop(paste("Application error:", result$error$message))
  if (is.null(result$estimates)) stop("Expected an engine result with estimates")
  check("method", result$method, method, 0)
  d <- records(request$rows)
  original <- names(d)
  # Different private identifiers from the application avoid relying on its
  # renaming implementation and permit arbitrary original column names.
  prefix <- "reference_variable_"
  literals <- c(original, strings(plan$options$factor_levels), strings(plan$options$group_levels))
  while (any(grepl(prefix, literals, fixed = TRUE))) prefix <- paste0(prefix, "x")
  private <- sprintf("%s%08d", prefix, seq_along(original))
  names(d) <- private
  col <- function(x) {
    at <- match(x, original)
    if (length(at) != 1L || is.na(at)) stop(paste("Unknown column:", x))
    private[[at]]
  }
  cols <- function(x) vapply(strings(x), col, character(1), USE.NAMES = FALSE)
  outward <- function(x) {
    locations <- gregexpr(paste(private, collapse = "|"), x, perl = TRUE)
    regmatches(x, locations) <- lapply(regmatches(x, locations), function(z) original[match(z, private)])
    x
  }
  v <- plan$variables
  o <- plan$options
  for (k in names(o$factor_levels)) d[[col(k)]] <- factor(as.character(d[[col(k)]]), levels = strings(o$factor_levels[[k]]))
  y <- col(v$outcome)
  cv <- cols(v$covariates)
  selected <- unique(c(y, cv, cols(o$fixed_effects), unlist(lapply(
    intersect(c("treatment", "group", "moderator", "mediator", "time", "id", "cohort", "running", "weights", "cluster"), names(v)),
    function(k) col(v[[k]])), use.names = FALSE)))
  if (anyNA(d[selected])) stop("Reference input has missing selected values")
  level <- plan$confidence_level
  w <- if (is.null(v$weights)) rep(1, nrow(d)) else d[[col(v$weights)]]
  cluster <- if (is.null(v$cluster)) NULL else d[[col(v$cluster)]]
  set.seed(plan$seed)

  df_for <- function(residual_df) {
    if (identical(o$reference_distribution, "normal")) return(Inf)
    if (identical(o$df_method, "clusters_minus_one")) return(length(unique(cluster)) - 1L)
    residual_df
  }
  critical <- function(df) if (is.infinite(df)) stats::qnorm((1 + level) / 2) else stats::qt((1 + level) / 2, df)
  row_check <- function(rows, id, estimate, se, df = Inf, crit = critical(df), ci = NULL, p = NULL) {
    observed <- lookup(rows, id)
    check(paste0(id, ":estimate"), observed$estimate, unname(estimate))
    check(paste0(id, ":std_error"), observed$std_error, unname(se))
    available <- is.finite(estimate) && is.finite(se) && se > 0
    bounds <- if (!is.null(ci)) ci else if (available && is.finite(crit)) estimate + c(-1, 1) * crit * se else c(NA_real_, NA_real_)
    check(paste0(id, ":conf_low"), observed$conf_low, unname(bounds[[1L]]))
    check(paste0(id, ":conf_high"), observed$conf_high, unname(bounds[[2L]]))
    if (!is.null(p)) check(paste0(id, ":p_value"), observed$p_value, unname(p))
    else if ("p_value" %in% names(observed)) {
      pv <- if (!available) NA_real_ else if (is.infinite(df)) 2 * stats::pnorm(-abs(estimate / se)) else 2 * stats::pt(-abs(estimate / se), df)
      check(paste0(id, ":p_value"), observed$p_value, unname(pv))
    }
    if ("degrees_of_freedom" %in% names(observed)) check(paste0(id, ":degrees_of_freedom"), observed$degrees_of_freedom, if (is.finite(df)) df else NA_real_, 0)
    if ("statistic" %in% names(observed)) check(paste0(id, ":statistic"), observed$statistic, if (available) unname(estimate / se) else NA_real_)
    if ("log_p_value" %in% names(observed)) {
      lp <- if (!available) NA_real_ else log(2) + if (is.infinite(df)) stats::pnorm(-abs(estimate / se), log.p = TRUE) else stats::pt(-abs(estimate / se), df, log.p = TRUE)
      check(paste0(id, ":log_p_value"), observed$log_p_value, unname(lp))
    }
    invisible(observed)
  }
  gaussian_matrix_fit <- function(formula) {
    X <- stats::model.matrix(formula, d)
    response <- d[[y]]
    Xw <- X * sqrt(w)
    Q <- qr(Xw)
    if (Q$rank != ncol(X)) stop("Reference model is rank deficient")
    b <- qr.coef(Q, response * sqrt(w))
    residual <- response - as.vector(X %*% b)
    bread <- solve(crossprod(Xw))
    n <- nrow(X); k <- ncol(X)
    if (o$se_type == "classical") {
      V <- sum(w * residual^2) / (n - k) * bread
    } else if (o$se_type == "HC3") {
      hat <- w * rowSums((X %*% bread) * X)
      score <- X * as.vector(w * residual / (1 - hat))
      V <- bread %*% crossprod(score) %*% bread
    } else if (o$se_type == "cluster_HC1") {
      G <- length(unique(cluster))
      if (G < 2L) stop("Reference cluster covariance needs two groups")
      scores <- rowsum(X * as.vector(w * residual), group = cluster, reorder = FALSE)
      V <- G / (G - 1) * (n - 1) / (n - k) * bread %*% crossprod(scores) %*% bread
    } else stop("Unsupported covariance in matrix reference")
    dimnames(V) <- list(names(b), names(b))
    list(beta = b, covariance = V, formula = formula, X = X,
      residual_df = n - k, nobs = n, contrasts = attr(X, "contrasts"))
  }
  package_fit_reference <- function(formula) {
    fam <- get(o$family, envir = asNamespace("stats"))(link = o$link)
    if (o$estimator == "fixest") {
      package("fixest")
      fe <- cols(o$fixed_effects)
      if (length(fe)) formula <- stats::as.formula(paste(paste(deparse(formula), collapse = ""), "|", paste(fe, collapse = "+")))
      vc <- if (o$se_type == "classical") "iid" else stats::reformulate(col(v$cluster))
      fit <- if (o$family == "gaussian" && o$link == "identity")
        fixest::feols(formula, data = d, weights = w, vcov = vc, fixef.rm = "none", notes = FALSE) else
        fixest::feglm(formula, data = d, weights = w, family = fam, vcov = vc, fixef.rm = "none", notes = FALSE)
      V <- stats::vcov(fit)
    } else {
      fit <- stats::glm(formula, data = d, weights = w, family = fam, na.action = stats::na.fail)
      V <- switch(o$se_type, classical = stats::vcov(fit),
        HC3 = { package("sandwich"); sandwich::vcovHC(fit, type = "HC3") },
        cluster_HC1 = { package("sandwich"); sandwich::vcovCL(fit, cluster = cluster, type = "HC1", cadjust = TRUE) })
    }
    list(beta = stats::coef(fit), covariance = V, residual_df = stats::df.residual(fit), nobs = stats::nobs(fit))
  }
  coefficient_checks <- function(reference, rows) {
    b <- reference$beta; V <- reference$covariance
    check("coefficient_record_count", length(rows), length(b), 0)
    for (j in seq_along(b)) row_check(rows, paste0("coefficient:", outward(names(b)[[j]])), b[[j]], sqrt(V[j, j]), df_for(reference$residual_df))
    check("model_nobs", result$diagnostics$nobs, reference$nobs, 0)
    for (j in seq_along(b)) {
      name <- outward(names(b)[[j]])
      hits <- which(vapply(result$tables$covariance, function(z) identical(z$term, name), logical(1)))
      if (length(hits) != 1L) stop(paste("Missing covariance row:", name))
      obs <- result$tables$covariance[[hits]]$values
      check(paste0("covariance:", name), lapply(outward(names(b)), function(n) obs[[n]]), as.list(unname(V[j, ])))
    }
  }

  if (method %in% c("regression", "moderation")) {
    predictors <- unique(c(if (!is.null(v$treatment)) col(v$treatment), cv))
    formula <- if (method == "moderation") stats::reformulate(c(paste(col(v$treatment), col(v$moderator), sep = "*"), cv), response = y) else
      if (length(predictors)) stats::reformulate(predictors, response = y) else stats::as.formula(paste(y, "~ 1"))
    reference <- if (method == "moderation" || identical(o$estimator, "lm")) gaussian_matrix_fit(formula) else package_fit_reference(formula)
    coefficient_checks(reference, result$estimates)
    if (method == "moderation") {
      b <- reference$beta; V <- reference$covariance
      x <- col(v$treatment); z <- col(v$moderator)
      ix <- match(x, names(b)); ixz <- match(paste(x, z, sep = ":"), names(b))
      if (anyNA(c(ix, ixz))) stop("Missing continuous interaction terms")
      values <- vec(o$moderator_values)
      check("conditional_effect_count", length(result$tables$conditional_effects), length(values), 0)
      for (j in seq_along(values)) {
        # Includes twice the off-diagonal covariance term explicitly.
        estimate <- b[[ix]] + values[[j]] * b[[ixz]]
        variance <- V[ix, ix] + values[[j]]^2 * V[ixz, ixz] + 2 * values[[j]] * V[ix, ixz]
        row_check(result$tables$conditional_effects, paste0("conditional_effect:", j), estimate, sqrt(variance), df_for(reference$residual_df))
      }
    }
  } else if (method == "ancova") {
    g <- col(v$group); groups <- strings(o$group_levels)
    d[[g]] <- factor(as.character(d[[g]]), levels = groups)
    formula <- stats::reformulate(c(g, cv, paste(g, cols(o$group_interactions), sep = ":")[seq_along(cols(o$group_interactions))]), response = y)
    reference <- gaussian_matrix_fit(formula)
    coefficient_checks(reference, result$tables$coefficients)
    b <- reference$beta; V <- reference$covariance; df <- df_for(reference$residual_df)
    population <- d
    averaging <- if (identical(o$standardization_weights, "analysis_weights")) w else rep(1, nrow(d))
    if (o$adjustment == "at_values") {
      population <- d[1L, , drop = FALSE]
      averaging <- 1
      for (name in names(o$covariate_values)) {
        key <- col(name); value <- o$covariate_values[[name]]
        population[[key]] <- if (is.factor(d[[key]])) factor(value, levels = levels(d[[key]])) else value
      }
    }
    averaging <- averaging / sum(averaging)
    L <- matrix(NA_real_, nrow = length(groups), ncol = length(b), dimnames = list(groups, names(b)))
    no_response <- stats::delete.response(stats::terms(formula))
    for (j in seq_along(groups)) {
      population[[g]] <- factor(rep(groups[[j]], nrow(population)), levels = groups)
      counterfactual <- stats::model.matrix(no_response, population, contrasts.arg = reference$contrasts)
      L[j, ] <- as.numeric(crossprod(averaging, counterfactual))
      estimate <- sum(averaging * as.vector(counterfactual %*% b))
      se <- sqrt(as.numeric(L[j, ] %*% V %*% L[j, ]))
      row_check(result$estimates, paste0("adjusted_mean:", j), estimate, se, df)
    }
    check("ancova_estimate_count", length(result$estimates), length(groups) + length(o$contrasts), 0)
    rawp <- numeric(length(o$contrasts))
    for (j in seq_along(o$contrasts)) {
      ct <- o$contrasts[[j]]
      contrast <- L[ct$numerator, ] - L[ct$denominator, ]
      estimate <- sum(contrast * b); se <- sqrt(as.numeric(contrast %*% V %*% contrast))
      row_check(result$estimates, paste0("group_contrast:", ct$id), estimate, se, df)
      rawp[[j]] <- if (is.infinite(df)) 2 * stats::pnorm(-abs(estimate / se)) else 2 * stats::pt(-abs(estimate / se), df)
    }
    if (length(rawp)) {
      adj <- stats::p.adjust(rawp, method = o$p_adjust)
      for (j in seq_along(adj)) check(paste0("adjusted_p:", o$contrasts[[j]]$id), lookup(result$estimates, paste0("group_contrast:", o$contrasts[[j]]$id))$p_value_adjusted, adj[[j]])
    }
    joint <- L[-1L, , drop = FALSE] - matrix(L[1L, ], nrow = length(groups) - 1L, ncol = ncol(L), byrow = TRUE)
    delta <- as.vector(joint %*% b); jointV <- joint %*% V %*% t(joint)
    wald <- as.numeric(crossprod(delta, solve(jointV, delta)))
    check("joint_group_wald", result$tables$joint_group_test[[1L]]$wald_chisq, wald)
  } else if (method == "matching") {
    pair_rows <- result$tables$pairs
    ti <- vapply(pair_rows, function(p) p$treated_row_index, numeric(1))
    ci <- vapply(pair_rows, function(p) p$control_row_index, numeric(1))
    if (!length(ti) || any(!c(ti, ci) %in% seq_len(nrow(d)))) stop("Invalid source-row matching indices")
    tx <- d[[col(v$treatment)]]
    check("pairs_treated_membership", tx[ti], rep(1, length(ti)), 0)
    check("pairs_control_membership", tx[ci], rep(0, length(ci)), 0)
    check("pairs_no_replacement", anyDuplicated(c(ti, ci)), 0L, 0)
    delta <- d[[y]][ti] - d[[y]][ci]
    check("pair_difference_from_source", lapply(pair_rows, function(p) p$difference), as.list(delta))
    check("pair_treated_outcome_from_source", lapply(pair_rows, function(p) p$treated_outcome), as.list(d[[y]][ti]))
    check("pair_control_outcome_from_source", lapply(pair_rows, function(p) p$control_outcome), as.list(d[[y]][ci]))
    n <- length(delta)
    se <- if (n > 1L) sqrt(sum((delta - mean(delta))^2) / (n * (n - 1))) else NA_real_
    row_check(result$estimates, "matched_pair_mean_difference", sum(delta) / n, se, n - 1L)
    check("pair_count", result$diagnostics$pair_count, n, 0)
    package("MatchIt")
    rownames(d) <- as.character(seq_len(nrow(d)))
    fm <- stats::reformulate(cv, response = col(v$treatment))
    matched <- MatchIt::matchit(fm, data = d, method = o$method, distance = o$distance,
      link = o$link, estimand = o$estimand, replace = o$replace, ratio = o$ratio,
      caliper = o$caliper, std.caliper = o$std_caliper, m.order = o$m_order)
    matrix <- matched$match.matrix
    retained <- which(!is.na(matrix[, 1L]))
    check("matchit_treated_row_indices", ti, as.integer(rownames(matrix)[retained]), 0)
    check("matchit_control_row_indices", ci, as.integer(matrix[retained, 1L]), 0)
    check("matched_estimate_count", length(result$estimates), 1L, 0)
  } else if (method == "did") {
    package("did")
    if (isTRUE(o$panel)) {
      id <- col(v$id)
      d[[id]] <- match(d[[id]], unique(d[[id]]))
    } else {
      id <- paste0(prefix, "observation_index")
      d[[id]] <- seq_len(nrow(d))
    }
    model <- if (length(cv)) stats::reformulate(cv) else ~1
    gt <- did::att_gt(yname = y, tname = col(v$time), idname = id, gname = col(v$cohort),
      xformla = model, data = d, panel = o$panel,
      allow_unbalanced_panel = isTRUE(o$panel) && isTRUE(o$allow_unbalanced_panel),
      control_group = o$control_group, anticipation = o$anticipation,
      est_method = o$est_method, base_period = o$base_period,
      bstrap = o$bstrap, biters = o$biters, cband = o$cband, alp = 1 - level,
      clustervars = if (is.null(v$cluster)) NULL else col(v$cluster),
      weightsname = if (is.null(v$weights)) NULL else col(v$weights), print_details = FALSE, pl = FALSE)
    band <- if (isTRUE(o$cband)) if (length(gt$c) == 1L && is.finite(gt$c)) gt$c else NA_real_ else critical(Inf)
    check("group_time_record_count", length(result$tables$group_time_effects), length(gt$att), 0)
    for (j in seq_along(gt$att)) row_check(result$tables$group_time_effects,
      paste0("att_gt:", gt$group[[j]], ":", gt$t[[j]]), gt$att[[j]], gt$se[[j]], crit = band)
    types <- strings(o$aggregations)
    check("did_aggregation_count", length(result$estimates), length(types), 0)
    for (type in types) {
      a <- list(MP = gt, type = type, bstrap = o$bstrap, biters = o$biters,
        cband = o$cband, alp = 1 - level, na.rm = FALSE)
      for (name in intersect(c("min_e", "max_e"), names(o))) a[[name]] <- o[[name]]
      ag <- do.call(did::aggte, a)
      row_check(result$estimates, paste0("att_overall:", type), ag$overall.att, ag$overall.se)
      if (length(ag$egt)) {
        rows <- result$tables[[paste0(type, "_effects")]]
        band <- if (isTRUE(o$cband)) if (length(ag$crit.val.egt) == 1L && is.finite(ag$crit.val.egt)) ag$crit.val.egt else NA_real_ else critical(Inf)
        check(paste0(type, "_record_count"), length(rows), length(ag$egt), 0)
        for (j in seq_along(ag$egt)) row_check(rows, paste0("att_", type, ":", ag$egt[[j]]), ag$att.egt[[j]], ag$se.egt[[j]], crit = band)
      }
    }
  } else if (method == "rd") {
    package("rdrobust")
    a <- list(y = d[[y]], x = d[[col(v$running)]], c = o$cutoff, p = o$p, q = o$q,
      kernel = o$kernel, vce = o$vce, masspoints = o$masspoints, covs_drop = FALSE, level = 100 * level)
    # `$bandwidth` partially matches `bandwidth_method` in an R list. Test
    # exact key membership so automatic selection is never sent as numeric h.
    if ("bandwidth" %in% names(o)) {
      a$h <- vec(o[["bandwidth"]]); a$b <- vec(o[["bias_bandwidth"]])
    } else a$bwselect <- o[["bandwidth_method"]]
    if (length(cv)) a$covs <- stats::model.matrix(stats::reformulate(cv), d)[, -1L, drop = FALSE]
    if (!is.null(v$weights)) a$weights <- w
    if (!is.null(v$cluster)) a$cluster <- cluster
    fit <- do.call(rdrobust::rdrobust, a)
    check("rd_estimate_count", length(result$estimates), nrow(fit$coef), 0)
    for (j in seq_len(nrow(fit$coef))) row_check(result$estimates, paste0("rd:", j), fit$coef[j, 1L], fit$se[j, 1L], ci = fit$ci[j, ], p = fit$pv[j, 1L])
    for (j in seq_len(nrow(fit$bws))) {
      check(paste0("bandwidth:", rownames(fit$bws)[[j]], ":left"), result$tables$bandwidths[[j]]$left, fit$bws[j, 1L])
      check(paste0("bandwidth:", rownames(fit$bws)[[j]], ":right"), result$tables$bandwidths[[j]]$right, fit$bws[j, 2L])
    }
    check("rd_left_n", result$diagnostics$n_left, fit$N[[1L]], 0)
    check("rd_right_n", result$diagnostics$n_right, fit$N[[2L]], 0)
  } else if (method == "mediation") {
    package("lavaan")
    x <- col(v$treatment); mediator <- col(v$mediator)
    suffix <- if (length(cv)) paste0(" + ", paste(cv, collapse = " + ")) else ""
    model <- paste0(mediator, " ~ a*", x, suffix, "\n", y, " ~ direct*", x, " + b*", mediator, suffix,
      "\nindirect := a*b\ntotal := direct + a*b")
    fit <- lavaan::sem(model, data = d, estimator = o$estimator, se = "bootstrap",
      bootstrap = o$bootstrap_samples, fixed.x = o$fixed_x, missing = "listwise")
    pe <- lavaan::parameterEstimates(fit, level = level, ci = TRUE, boot.ci.type = o$bootstrap_ci, standardized = FALSE)
    pe <- pe[pe$op %in% c("~", ":="), , drop = FALSE]
    check("mediation_estimate_count", length(result$estimates), nrow(pe), 0)
    for (j in seq_len(nrow(pe))) {
      r <- pe[j, ]
      term <- if (r$op == ":=") r$lhs else paste(outward(r$lhs), "~", outward(r$rhs))
      id <- paste0("mediation:", if (nzchar(r$label)) r$label else term)
      observed <- lookup(result$estimates, id)
      check(paste0(id, ":estimate"), observed$estimate, r$est)
      check(paste0(id, ":std_error"), observed$std_error, r$se)
      check(paste0(id, ":conf_low"), observed$conf_low, r$ci.lower)
      check(paste0(id, ":conf_high"), observed$conf_high, r$ci.upper)
    }
    a <- lookup(result$estimates, "mediation:a")$estimate
    b <- lookup(result$estimates, "mediation:b")$estimate
    direct <- lookup(result$estimates, "mediation:direct")$estimate
    check("indirect_product_identity", lookup(result$estimates, "mediation:indirect")$estimate, a * b)
    check("total_sum_identity", lookup(result$estimates, "mediation:total")$estimate, direct + a * b)
    check("bootstrap_requested", result$diagnostics$bootstrap_requested, o$bootstrap_samples, 0)
    check("mediation_nobs", result$diagnostics$nobs, lavaan::lavInspect(fit, "nobs"), 0)
  } else stop(paste("Unsupported reference method:", method))
  invisible(NULL)
}

tryCatch(withCallingHandlers({
  if (length(argv) != 2L) stop("Usage: check_reference.R request.json result.json")
  request <- jsonlite::fromJSON(argv[[1L]], simplifyVector = FALSE)
  result <- jsonlite::fromJSON(argv[[2L]], simplifyVector = FALSE)
  # Keep stdout as one JSON object even when packages print progress.
  invisible(capture.output(run_reference(request, result), type = "output"))
}, warning = function(w) invokeRestart("muffleWarning"), message = function(m) invokeRestart("muffleMessage")),
error = function(e) check("reference_execution", conditionMessage(e), "completed", 0))
passed <- length(checks) > 0L && all(vapply(checks, function(z) isTRUE(z$match), logical(1)))
cat(jsonlite::toJSON(list(method = method, checks = checks, passed = passed),
  auto_unbox = TRUE, null = "null", na = "null", digits = NA, force = TRUE))
quit(status = if (passed) 0L else 1L)
